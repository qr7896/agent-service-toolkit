import argparse
import asyncio
import hashlib
import json
import tempfile
import time
from pathlib import Path

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

MODEL_ID = DeepseekModelName.DEEPSEEK_V4_FLASH
TOKEN_BUDGET = 8_000
MAX_OUTPUT_TOKENS = 1_000
EVIDENCE_PROTOCOL = "declared-seed-read-v1"
CONFIG = AutonomousConfig(model_mode="deepseek-live", max_iterations=1)
RESULT_PATH = Path("evals/results/e1b_autonomous_dev_run.json")


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


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume-budget", type=int, default=0)
    args = parser.parse_args()
    model = get_model(MODEL_ID).bind(temperature=0, max_tokens=MAX_OUTPUT_TOKENS)
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
                response = await model.ainvoke(build_messages(payload))
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
            except (json.JSONDecodeError, TypeError, ValueError, PermissionError) as exc:
                row.update(resolved=False, failure="parse_failure", error=str(exc))
            except Exception as exc:
                row.update(resolved=False, failure="model_failure", error=str(exc))
            row["wall_time_ms"] = round((time.perf_counter() - started) * 1000, 1)
            rows.append(row)
            write_dev_run(str(MODEL_ID), rows, config=CONFIG)
            print(json.dumps({"task": task.instance_id, "spent": spent, **row}, ensure_ascii=False))
            if row.get("failure") == "model_failure":
                break
    report = write_dev_run(str(MODEL_ID), rows, config=CONFIG)
    report["execution"] = {
        "temperature": 0,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "original_token_budget": TOKEN_BUDGET,
        "additional_token_budget": args.resume_budget,
        "token_ceiling": token_ceiling,
        "max_iterations": CONFIG.max_iterations,
        "evidence_protocol": EVIDENCE_PROTOCOL,
        "provider": "deepseek",
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
