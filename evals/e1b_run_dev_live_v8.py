import hashlib
import json
import tempfile
import time

import evals.e1b_run_dev_live_v7 as base
from evals.e1b_autonomous_harness import (
    apply_patch,
    dev_tasks,
    parse_patch_response,
    sanitize_editor_payload,
)
from evals.e1b_contract_coverage_v7 import (
    audit_patch_coverage,
    build_coverage_contract,
    require_patch_coverage,
)
from evals.e1b_contract_extractor_v6 import extract_contract
from evals.e1b_editor_adapter import content_text
from evals.e1b_editor_adapter_v7 import build_proposal_messages, build_review_messages
from evals.e1b_state_transition_v8 import (
    audit_state_transition_contract,
    build_transition_contract,
    require_state_transition_contract,
)
from evals.swe_tasks import grade, prepare

RUN_ID = "e1b-r10-dev-v8"
RESULT_SCHEMA = "e1b-r10-v8-result-v1"
TRANSITION_SCHEMA = "e1b-state-transition-v1"
EVIDENCE_PROTOCOL = "declared-seed-read-v7-coverage-state-transition"
LEDGER_PATH = base.Path(".codex/e1b/r10-v8/provider_calls.jsonl")
RESULT_PATH = base.Path("evals/results/e1b_autonomous_dev_run_v8.json")
MAX_OUTPUT_TOKENS = 550


def build_report(rows):
    report = base.write_dev_run(str(base.base.MODEL_ID), rows, config=base.base.CONFIG, output=RESULT_PATH)
    report["result_schema"] = RESULT_SCHEMA
    report["execution"] = {
        "result_schema": RESULT_SCHEMA,
        "transition_schema": TRANSITION_SCHEMA,
        "evidence_protocol": EVIDENCE_PROTOCOL,
        "provider_run_id": RUN_ID,
        "provider_ledger_path": str(LEDGER_PATH),
        "contract_coverage_enforced": True,
        "state_transition_enforced": True,
        "test_outcomes_opened": 0,
        "freeze_gate": "4/4 resolved + protocol valid + no regression",
    }
    RESULT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def provider_config(task_id):
    config = base.provider_config(task_id)
    configurable = config["configurable"]
    configurable["provider_ledger_path"] = str(LEDGER_PATH)
    configurable["provider_run_id"] = RUN_ID
    return config


async def invoke_v8(model, messages, task_id, role):
    response = await base.base.budgeted_ainvoke(model, messages, provider_config(task_id), role=role)
    return response, base.base.usage_tokens(response)


def verify_candidate(payload, patch):
    behavioral = extract_contract(payload["problem_statement"])
    coverage = build_coverage_contract(payload, behavioral)
    transition = build_transition_contract(behavioral)
    try:
        coverage_report = require_patch_coverage(coverage, patch)
    except ValueError as exc:
        error = CoverageGateFailure(str(exc))
        error.audit = audit_patch_coverage(coverage, patch)
        raise error from exc
    try:
        transition_report = require_state_transition_contract(transition, patch)
    except ValueError as exc:
        error = TransitionGateFailure(str(exc))
        error.audit = audit_state_transition_contract(transition, patch)
        raise error from exc
    return coverage_report, transition_report


def preflight():
    report = base.preflight()
    report.update(
        protocol="e1b-r10-v8-state-transition-dev-preflight-v1",
        result_schema=RESULT_SCHEMA,
        transition_schema=TRANSITION_SCHEMA,
        result_exists=RESULT_PATH.exists(),
        ledger_exists=LEDGER_PATH.exists(),
        live_authorized=False,
        provider_calls=0,
    )
    reserves_fit = all(
        row.get("proposal_reserve_fits") is True and row.get("review_reserve_fits") is True
        for row in report["rows"]
    )
    report["ready"] = reserves_fit and not report["result_exists"] and not report["ledger_exists"]
    return report


async def main():
    parser = base.argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(), ensure_ascii=False, indent=2))
        return
    if RESULT_PATH.exists() or LEDGER_PATH.exists():
        raise FileExistsError("R10 v8 DEV artifacts already exist; refusing to overwrite or rerun")

    model = base.base.get_model(base.base.MODEL_ID)
    rows = []
    with tempfile.TemporaryDirectory(prefix="e1b-live-dev-v8-") as directory:
        root_base = base.Path(directory)
        for task in dev_tasks():
            root = root_base / task.instance_id
            prepare(task, root)
            before = grade(task, root)
            payload = sanitize_editor_payload(task, base.evidence_for(task, root))
            started = time.perf_counter()
            row = {
                "result_schema": RESULT_SCHEMA,
                "transition_schema": TRANSITION_SCHEMA,
                "instance_id": task.instance_id,
                "base_resolved": before["resolved"],
                "model_calls": 0,
                "evidence_protocol": EVIDENCE_PROTOCOL,
            }
            try:
                proposal_response, proposal_usage = await invoke_v8(
                    model, build_proposal_messages(payload), task.instance_id, "compact_editor_proposal"
                )
                row["model_calls"] += 1
                row.update(proposal_usage)
                proposal_patch = parse_patch_response(content_text(proposal_response))
                row["proposal_coverage"], row["proposal_transition"] = verify_candidate(payload, proposal_patch)

                review_response, review_usage = await invoke_v8(
                    model, build_review_messages(payload, proposal_patch), task.instance_id, "compact_editor_review"
                )
                row["model_calls"] += 1
                for key in ("input_tokens", "output_tokens", "total_tokens"):
                    row[key] += review_usage[key]
                patch = parse_patch_response(content_text(review_response))
                row["final_coverage"], row["final_transition"] = verify_candidate(payload, patch)

                row["proposal_patch_sha256"] = hashlib.sha256(
                    json.dumps(proposal_patch, sort_keys=True).encode()
                ).hexdigest()
                row["patch_sha256"] = hashlib.sha256(json.dumps(patch, sort_keys=True).encode()).hexdigest()
                row["review_changed_patch"] = proposal_patch != patch
                row["files_written"] = apply_patch(root, patch)
                after = grade(task, root)
                row.update(
                    resolved=after["resolved"],
                    fail_to_pass=after["fail_to_pass"],
                    pass_to_pass=after["pass_to_pass"],
                    failure=None,
                )
            except CoverageGateFailure as exc:
                row.update(resolved=False, failure="contract_coverage_failure", error=str(exc))
                row["rejected_gate_audit"] = exc.audit
            except TransitionGateFailure as exc:
                row.update(resolved=False, failure="state_transition_failure", error=str(exc))
                row["rejected_gate_audit"] = exc.audit
            except base.base.ProviderBudgetExceeded as exc:
                row.update(resolved=False, failure="budget_exhaustion", error=str(exc))
            except base.base.AmbiguousProviderCall as exc:
                row.update(resolved=False, failure="model_failure", error=str(exc))
            except (json.JSONDecodeError, TypeError, PermissionError) as exc:
                row.update(resolved=False, failure="parse_failure", error=str(exc))
            except Exception as exc:
                row.update(resolved=False, failure="model_failure", error=str(exc))
            row["wall_time_ms"] = round((time.perf_counter() - started) * 1000, 1)
            rows.append(row)
            build_report(rows)
            if row.get("failure") in {"model_failure", "budget_exhaustion"}:
                break

    build_report(rows)


class CoverageGateFailure(ValueError):
    pass


class TransitionGateFailure(ValueError):
    pass


if __name__ == "__main__":
    base.asyncio.run(main())
