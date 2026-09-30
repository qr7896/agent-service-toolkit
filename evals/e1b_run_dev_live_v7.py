import hashlib
import json
import tempfile
import time

import evals.e1b_run_dev_live_v4 as base
from evals.e1b_autonomous_harness import (
    apply_patch,
    dev_tasks,
    parse_patch_response,
    sanitize_editor_payload,
)
from evals.e1b_autonomous_runlog import write_dev_run
from evals.e1b_contract_coverage_v7 import build_coverage_contract, require_patch_coverage
from evals.e1b_contract_extractor_v6 import extract_contract
from evals.e1b_editor_adapter import content_text
from evals.e1b_editor_adapter_v7 import build_proposal_messages, build_review_messages
from evals.e1b_run_dev_live_v4 import *  # noqa: F403
from evals.swe_tasks import grade, prepare

RUN_ID = "e1b-r10-dev-v7b"
MAX_OUTPUT_TOKENS = 550
EVIDENCE_PROTOCOL = "declared-seed-read-v6-contract-coverage"
LEDGER_PATH = Path(".codex/e1b/r10-v7b/provider_calls.jsonl")  # noqa: F405
RESULT_PATH = Path("evals/results/e1b_autonomous_dev_run_v7b.json")  # noqa: F405
V4_EVIDENCE_FOR = base.evidence_for


def provider_config(task_id):
    return {
        "configurable": {
            "provider_ledger_path": str(LEDGER_PATH),
            "provider_run_id": RUN_ID,
            "provider_task_id": task_id,
            "provider_total_token_ceiling": TOKEN_BUDGET,  # noqa: F405
            "provider_task_token_ceiling": TASK_TOKEN_CEILING,  # noqa: F405
            "provider_max_calls_per_task": 2,
            "provider_max_output_tokens": MAX_OUTPUT_TOKENS,
            "provider_prompt_reserve_multiplier": PROMPT_RESERVE_MULTIPLIER,  # noqa: F405
            "provider_disable_thinking": True,
        }
    }


def evidence_for(task, root):
    payload = V4_EVIDENCE_FOR(task, root)
    payload["protocol"] = EVIDENCE_PROTOCOL
    return payload


async def invoke_v7(model, messages, task_id, role):
    response = await base.budgeted_ainvoke(model, messages, provider_config(task_id), role=role)
    return response, base.usage_tokens(response)


def preflight():
    original = (
        base.RUN_ID, base.MAX_OUTPUT_TOKENS, base.EVIDENCE_PROTOCOL, base.LEDGER_PATH,
        base.RESULT_PATH, base.provider_config, base.evidence_for,
        base.build_proposal_messages, base.build_review_messages,
    )
    try:
        base.RUN_ID = RUN_ID
        base.MAX_OUTPUT_TOKENS = MAX_OUTPUT_TOKENS
        base.EVIDENCE_PROTOCOL = EVIDENCE_PROTOCOL
        base.LEDGER_PATH = LEDGER_PATH
        base.RESULT_PATH = RESULT_PATH
        base.provider_config = provider_config
        base.evidence_for = evidence_for
        base.build_proposal_messages = build_proposal_messages
        base.build_review_messages = build_review_messages
        report = base.preflight()
        report["protocol"] = "e1b-r10-contract-coverage-dev-preflight-v1"
        report["result_exists"] = RESULT_PATH.exists()
        report["ledger_exists"] = LEDGER_PATH.exists()
        report["ready"] = report["ready"] and not report["result_exists"] and not report["ledger_exists"]
        return report
    finally:
        (
            base.RUN_ID, base.MAX_OUTPUT_TOKENS, base.EVIDENCE_PROTOCOL, base.LEDGER_PATH,
            base.RESULT_PATH, base.provider_config, base.evidence_for,
            base.build_proposal_messages, base.build_review_messages,
        ) = original


async def main():
    parser = argparse.ArgumentParser()  # noqa: F405
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(), ensure_ascii=False, indent=2))  # noqa: F405
        return
    if RESULT_PATH.exists() or LEDGER_PATH.exists():
        raise FileExistsError("R10 v7 DEV artifacts already exist; refusing to overwrite or rerun")

    model = base.get_model(base.MODEL_ID)
    rows = []
    spent = 0
    with tempfile.TemporaryDirectory(prefix="e1b-live-dev-v7-") as directory:
        root_base = Path(directory)  # noqa: F405
        for task in dev_tasks():
            root = root_base / task.instance_id
            prepare(task, root)
            before = grade(task, root)
            payload = sanitize_editor_payload(task, evidence_for(task, root))
            coverage = build_coverage_contract(payload, extract_contract(payload["problem_statement"]))
            started = time.perf_counter()
            row = {"instance_id": task.instance_id, "base_resolved": before["resolved"], "model_calls": 0, "evidence_protocol": EVIDENCE_PROTOCOL}
            try:
                proposal_response, proposal_usage = await invoke_v7(model, build_proposal_messages(payload), task.instance_id, "compact_editor_proposal")
                row["model_calls"] += 1
                row.update(proposal_usage)
                spent += proposal_usage["total_tokens"]
                proposal_patch = parse_patch_response(content_text(proposal_response))
                row["proposal_coverage"] = require_patch_coverage(coverage, proposal_patch)
                review_response, review_usage = await invoke_v7(model, build_review_messages(payload, proposal_patch), task.instance_id, "compact_editor_review")
                row["model_calls"] += 1
                for key in ("input_tokens", "output_tokens", "total_tokens"):
                    row[key] += review_usage[key]
                spent += review_usage["total_tokens"]
                patch = parse_patch_response(content_text(review_response))
                row["final_coverage"] = require_patch_coverage(coverage, patch)
                row["proposal_patch_sha256"] = hashlib.sha256(json.dumps(proposal_patch, sort_keys=True).encode()).hexdigest()
                row["patch_sha256"] = hashlib.sha256(json.dumps(patch, sort_keys=True).encode()).hexdigest()
                row["review_changed_patch"] = proposal_patch != patch
                row["files_written"] = apply_patch(root, patch)
                after = grade(task, root)
                row.update(resolved=after["resolved"], fail_to_pass=after["fail_to_pass"], pass_to_pass=after["pass_to_pass"], failure=None)
            except ValueError as exc:
                row.update(resolved=False, failure="contract_coverage_failure", error=str(exc))
            except base.ProviderBudgetExceeded as exc:
                row.update(resolved=False, failure="budget_exhaustion", error=str(exc))
            except base.AmbiguousProviderCall as exc:
                row.update(resolved=False, failure="model_failure", error=str(exc))
            except (json.JSONDecodeError, TypeError, PermissionError) as exc:  # noqa: F405
                row.update(resolved=False, failure="parse_failure", error=str(exc))
            except Exception as exc:
                row.update(resolved=False, failure="model_failure", error=str(exc))
            row["wall_time_ms"] = round((time.perf_counter() - started) * 1000, 1)
            rows.append(row)
            write_dev_run(str(base.MODEL_ID), rows, config=base.CONFIG, output=RESULT_PATH)
            print(json.dumps({"task": task.instance_id, "spent": spent, **row}, ensure_ascii=False))  # noqa: F405
            if row.get("failure") in {"model_failure", "budget_exhaustion"}:
                break

    report = write_dev_run(str(base.MODEL_ID), rows, config=base.CONFIG, output=RESULT_PATH)
    report["execution"] = {"temperature": 0, "max_output_tokens": MAX_OUTPUT_TOKENS, "task_token_ceiling": TASK_TOKEN_CEILING, "original_token_budget": TOKEN_BUDGET, "max_iterations": base.CONFIG.max_iterations, "evidence_protocol": EVIDENCE_PROTOCOL, "provider": "deepseek", "provider_run_id": RUN_ID, "provider_ledger_path": str(LEDGER_PATH), "thinking_disabled": True, "seed": None, "sandbox_required": True, "contract_coverage_enforced": True, "test_outcomes_opened": 0}  # noqa: F405
    RESULT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))  # noqa: F405


if __name__ == "__main__":
    asyncio.run(main())  # noqa: F405
