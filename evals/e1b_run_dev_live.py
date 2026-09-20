import argparse
import asyncio
import hashlib
import json
import math
import tempfile
import time
from pathlib import Path

from agents.model_budget import (
    AmbiguousProviderCall,
    ProviderBudgetExceeded,
    _prompt_text,
    budgeted_ainvoke,
)
from agents.model_router import estimate_tokens
from core import get_model
from evals.e1b_autonomous_harness import (
    apply_patch,
    dev_tasks,
    parse_patch_response,
    sanitize_editor_payload,
)
from evals.e1b_autonomous_protocol import AutonomousConfig
from evals.e1b_autonomous_runlog import write_dev_run
from evals.e1b_editor_adapter import build_messages, content_text, usage_tokens
from evals.evidence_runtime import EvidenceLedger, WorkspaceRetrievalAdapter
from evals.safe_workspace import SafeWorkspace
from evals.swe_tasks import grade, prepare
from schema.models import DeepseekModelName

MODEL_ID = DeepseekModelName.DEEPSEEK_FLASH
RUN_ID = "e1b-r10-dev-v2"
TOKEN_BUDGET = 8_800
TASK_TOKEN_CEILING = 2_200
MAX_OUTPUT_TOKENS = 600
PROMPT_RESERVE_MULTIPLIER = 2.0
EVIDENCE_PROTOCOL = "declared-seed-read-v1"
CONFIG = AutonomousConfig(model_mode="deepseek-live", max_iterations=1)
LEDGER_PATH = Path(".codex/e1b/r10-v2/provider_calls.jsonl")
RESULT_PATH = Path("evals/results/e1b_autonomous_dev_run_v2.json")


def evidence_for(task, root):
    workspace = SafeWorkspace(root, max_read_calls=3, max_total_bytes=20_000)
    ledger = EvidenceLedger()
    adapter = WorkspaceRetrievalAdapter(workspace, ledger)
    for path in sorted(task.setup_files):
        adapter.read(path)
    return {
        "protocol": EVIDENCE_PROTOCOL,
        "items": ledger.payload(),
        "ledger": ledger.summary(),
        "workspace": workspace.evidence_summary(),
    }


def resume_state(additional_budget):
    report = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    pending = {
        row["instance_id"] for row in report["rows"] if row.get("failure") == "budget_exhaustion"
    }
    rows = [row for row in report["rows"] if row["instance_id"] not in pending]
    spent = int(report["summary"]["total_tokens"])
    return rows, pending, spent, spent + additional_budget


def provider_config(task_id, total_ceiling=TOKEN_BUDGET):
    return {
        "configurable": {
            "provider_ledger_path": str(LEDGER_PATH),
            "provider_run_id": RUN_ID,
            "provider_task_id": task_id,
            "provider_total_token_ceiling": total_ceiling,
            "provider_task_token_ceiling": TASK_TOKEN_CEILING,
            "provider_max_calls_per_task": 1,
            "provider_max_output_tokens": MAX_OUTPUT_TOKENS,
            "provider_prompt_reserve_multiplier": PROMPT_RESERVE_MULTIPLIER,
            "provider_disable_thinking": True,
        }
    }


def preflight():
    rows = []
    with tempfile.TemporaryDirectory(prefix="e1b-r10-v2-preflight-") as directory:
        base = Path(directory)
        for task in dev_tasks():
            root = base / task.instance_id
            prepare(task, root)
            payload = sanitize_editor_payload(task, evidence_for(task, root))
            prompt_tokens = estimate_tokens(_prompt_text(build_messages(payload)))
            reserve = math.ceil(prompt_tokens * PROMPT_RESERVE_MULTIPLIER) + MAX_OUTPUT_TOKENS
            rows.append(
                {
                    "instance_id": task.instance_id,
                    "estimated_prompt_tokens": prompt_tokens,
                    "reserve": reserve,
                    "reserve_fits": reserve <= TASK_TOKEN_CEILING,
                }
            )
    return {
        "protocol": "e1b-r10-budgeted-dev-preflight-v1",
        "provider_calls": 0,
        "ready": all(row["reserve_fits"] for row in rows),
        "rows": rows,
    }


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume-budget", type=int, default=0)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(), ensure_ascii=False, indent=2))
        return
    if not args.resume_budget and (RESULT_PATH.exists() or LEDGER_PATH.exists()):
        raise FileExistsError("R10 v2 DEV artifacts already exist; refusing to overwrite or rerun")
    model = get_model(MODEL_ID)
    if args.resume_budget:
        rows, pending, spent, token_ceiling = resume_state(args.resume_budget)
        tasks = [task for task in dev_tasks() if task.instance_id in pending]
    else:
        rows, spent, token_ceiling = [], 0, TOKEN_BUDGET
        tasks = dev_tasks()
    with tempfile.TemporaryDirectory(prefix="e1b-live-dev-") as directory:
        base = Path(directory)
        for task in tasks:
            if spent >= token_ceiling:
                rows.append(
                    {
                        "instance_id": task.instance_id,
                        "model_calls": 0,
                        "resolved": False,
                        "failure": "budget_exhaustion",
                        "total_tokens": 0,
                        "wall_time_ms": 0,
                    }
                )
                continue
            root = base / task.instance_id
            prepare(task, root)
            before = grade(task, root)
            payload = sanitize_editor_payload(task, evidence_for(task, root))
            started = time.perf_counter()
            row = {
                "instance_id": task.instance_id,
                "base_resolved": before["resolved"],
                "model_calls": 1,
                "evidence_protocol": EVIDENCE_PROTOCOL,
            }
            try:
                response = await budgeted_ainvoke(
                    model,
                    build_messages(payload),
                    provider_config(task.instance_id, token_ceiling),
                    role="compact_editor",
                )
                usage = usage_tokens(response)
                row.update(usage)
                spent += usage["total_tokens"]
                patch = parse_patch_response(content_text(response))
                row["patch_sha256"] = hashlib.sha256(
                    json.dumps(patch, sort_keys=True).encode()
                ).hexdigest()
                row["files_written"] = apply_patch(root, patch)
                after = grade(task, root)
                row.update(
                    resolved=after["resolved"],
                    fail_to_pass=after["fail_to_pass"],
                    pass_to_pass=after["pass_to_pass"],
                    failure=None,
                )
            except ProviderBudgetExceeded as exc:
                row.update(resolved=False, failure="budget_exhaustion", error=str(exc))
            except AmbiguousProviderCall as exc:
                row.update(resolved=False, failure="model_failure", error=str(exc))
            except (json.JSONDecodeError, TypeError, ValueError, PermissionError) as exc:
                row.update(resolved=False, failure="parse_failure", error=str(exc))
            except Exception as exc:
                row.update(resolved=False, failure="model_failure", error=str(exc))
            row["wall_time_ms"] = round((time.perf_counter() - started) * 1000, 1)
            rows.append(row)
            write_dev_run(str(MODEL_ID), rows, config=CONFIG, output=RESULT_PATH)
            print(json.dumps({"task": task.instance_id, "spent": spent, **row}, ensure_ascii=False))
            if row.get("failure") == "model_failure":
                break
    report = write_dev_run(str(MODEL_ID), rows, config=CONFIG, output=RESULT_PATH)
    report["execution"] = {
        "temperature": 0,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "task_token_ceiling": TASK_TOKEN_CEILING,
        "prompt_reserve_multiplier": PROMPT_RESERVE_MULTIPLIER,
        "original_token_budget": TOKEN_BUDGET,
        "additional_token_budget": args.resume_budget,
        "token_ceiling": token_ceiling,
        "max_iterations": CONFIG.max_iterations,
        "evidence_protocol": EVIDENCE_PROTOCOL,
        "provider": "deepseek",
        "provider_run_id": RUN_ID,
        "provider_ledger_path": str(LEDGER_PATH),
        "thinking_disabled": True,
        "seed": None,
        "sandbox_required": True,
        "budget_status": "within_limit" if spent <= token_ceiling else "exceeded_after_atomic_call",
        "budget_overrun_tokens": max(0, spent - token_ceiling),
        "test_outcomes_opened": 0,
    }
    RESULT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
