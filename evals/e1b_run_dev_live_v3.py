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
from evals.e1b_editor_adapter import (
    build_messages,
    build_review_messages,
    content_text,
    usage_tokens,
)
from evals.evidence_runtime import EvidenceLedger, WorkspaceRetrievalAdapter
from evals.safe_workspace import SafeWorkspace
from evals.swe_tasks import grade, prepare
from schema.models import DeepseekModelName

MODEL_ID = DeepseekModelName.DEEPSEEK_FLASH
RUN_ID = "e1b-r10-dev-v3"
TOKEN_BUDGET = 16_000
TASK_TOKEN_CEILING = 4_000
MAX_OUTPUT_TOKENS = 600
PROMPT_RESERVE_MULTIPLIER = 2.0
EVIDENCE_PROTOCOL = "declared-seed-read-v2-review"
CONFIG = AutonomousConfig(model_mode="deepseek-live", max_iterations=2)
LEDGER_PATH = Path(".codex/e1b/r10-v3/provider_calls.jsonl")
RESULT_PATH = Path("evals/results/e1b_autonomous_dev_run_v3.json")


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


def provider_config(task_id):
    return {
        "configurable": {
            "provider_ledger_path": str(LEDGER_PATH),
            "provider_run_id": RUN_ID,
            "provider_task_id": task_id,
            "provider_total_token_ceiling": TOKEN_BUDGET,
            "provider_task_token_ceiling": TASK_TOKEN_CEILING,
            "provider_max_calls_per_task": 2,
            "provider_max_output_tokens": MAX_OUTPUT_TOKENS,
            "provider_prompt_reserve_multiplier": PROMPT_RESERVE_MULTIPLIER,
            "provider_disable_thinking": True,
        }
    }


def reserve_for(messages):
    prompt_tokens = estimate_tokens(_prompt_text(messages))
    return {
        "estimated_prompt_tokens": prompt_tokens,
        "reserve": math.ceil(prompt_tokens * PROMPT_RESERVE_MULTIPLIER) + MAX_OUTPUT_TOKENS,
    }


def preflight():
    rows = []
    with tempfile.TemporaryDirectory(prefix="e1b-r10-v3-preflight-") as directory:
        base = Path(directory)
        for task in dev_tasks():
            root = base / task.instance_id
            prepare(task, root)
            payload = sanitize_editor_payload(task, evidence_for(task, root))
            proposal = reserve_for(build_messages(payload))
            placeholder = {"src/placeholder.py": "x" * (MAX_OUTPUT_TOKENS * 4)}
            review = reserve_for(build_review_messages(payload, placeholder))
            rows.append(
                {
                    "instance_id": task.instance_id,
                    "proposal": proposal,
                    "review_upper_bound_proxy": review,
                    "proposal_reserve_fits": proposal["reserve"] <= TASK_TOKEN_CEILING,
                    "review_reserve_fits": review["reserve"] <= TASK_TOKEN_CEILING,
                }
            )
    return {
        "protocol": "e1b-r10-two-pass-dev-preflight-v1",
        "provider_calls": 0,
        "ready": all(
            row["proposal_reserve_fits"] and row["review_reserve_fits"] for row in rows
        ),
        "rows": rows,
    }


async def invoke(model, messages, task_id, role):
    response = await budgeted_ainvoke(
        model,
        messages,
        provider_config(task_id),
        role=role,
    )
    return response, usage_tokens(response)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(), ensure_ascii=False, indent=2))
        return
    if RESULT_PATH.exists() or LEDGER_PATH.exists():
        raise FileExistsError("R10 v3 DEV artifacts already exist; refusing to overwrite or rerun")

    model = get_model(MODEL_ID)
    rows = []
    spent = 0
    with tempfile.TemporaryDirectory(prefix="e1b-live-dev-v3-") as directory:
        base = Path(directory)
        for task in dev_tasks():
            root = base / task.instance_id
            prepare(task, root)
            before = grade(task, root)
            payload = sanitize_editor_payload(task, evidence_for(task, root))
            started = time.perf_counter()
            row = {
                "instance_id": task.instance_id,
                "base_resolved": before["resolved"],
                "model_calls": 0,
                "evidence_protocol": EVIDENCE_PROTOCOL,
            }
            try:
                proposal_response, proposal_usage = await invoke(
                    model, build_messages(payload), task.instance_id, "compact_editor_proposal"
                )
                row["model_calls"] += 1
                row.update(proposal_usage)
                spent += proposal_usage["total_tokens"]
                proposal_patch = parse_patch_response(content_text(proposal_response))
                review_response, review_usage = await invoke(
                    model,
                    build_review_messages(payload, proposal_patch),
                    task.instance_id,
                    "compact_editor_review",
                )
                row["model_calls"] += 1
                for key in ("input_tokens", "output_tokens", "total_tokens"):
                    row[key] += review_usage[key]
                spent += review_usage["total_tokens"]
                patch = parse_patch_response(content_text(review_response))
                row["proposal_patch_sha256"] = hashlib.sha256(
                    json.dumps(proposal_patch, sort_keys=True).encode()
                ).hexdigest()
                row["patch_sha256"] = hashlib.sha256(
                    json.dumps(patch, sort_keys=True).encode()
                ).hexdigest()
                row["review_changed_patch"] = proposal_patch != patch
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
            if row.get("failure") in {"model_failure", "budget_exhaustion"}:
                break

    report = write_dev_run(str(MODEL_ID), rows, config=CONFIG, output=RESULT_PATH)
    report["execution"] = {
        "temperature": 0,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "task_token_ceiling": TASK_TOKEN_CEILING,
        "original_token_budget": TOKEN_BUDGET,
        "max_iterations": CONFIG.max_iterations,
        "evidence_protocol": EVIDENCE_PROTOCOL,
        "provider": "deepseek",
        "provider_run_id": RUN_ID,
        "provider_ledger_path": str(LEDGER_PATH),
        "thinking_disabled": True,
        "seed": None,
        "sandbox_required": True,
        "test_outcomes_opened": 0,
    }
    RESULT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
