import json
from pathlib import Path

V7 = Path("evals/results/e1b_autonomous_dev_run_v7b.json")
V8 = Path("evals/results/e1b_autonomous_dev_run_v8.json")
LEDGER = Path(".codex/e1b/r10-v8/provider_calls.jsonl")
OUT = Path("evals/results/e1b_autonomous_dev_v8_audit.json")
RESULT_SCHEMA = "e1b-r10-v8-result-v1"
TRANSITION_SCHEMA = "e1b-state-transition-v1"


def _row_gate_artifacts_valid(row):
    failure = row.get("failure")
    calls = int(row.get("model_calls", 0))
    if calls <= 0:
        return failure in {"model_failure", "budget_exhaustion", "parse_failure"}
    if failure in {"contract_coverage_failure", "state_transition_failure"} and calls == 1:
        return "final_coverage" not in row and "final_transition" not in row
    if calls >= 2 and failure in {"contract_coverage_failure", "state_transition_failure"}:
        return "proposal_coverage" in row and "proposal_transition" in row
    if failure is None:
        return all(
            key in row
            for key in ("proposal_coverage", "proposal_transition", "final_coverage", "final_transition")
        )
    return True


def audit(v7_report, v8_report, ledger_rows):
    before = {row["instance_id"]: row for row in v7_report["rows"]}
    after = {row["instance_id"]: row for row in v8_report["rows"]}
    common = sorted(set(before) & set(after))
    completed = [row for row in ledger_rows if row.get("status") == "completed"]
    started = [row for row in ledger_rows if row.get("status") == "started"]
    execution = v8_report.get("execution", {})
    completion_marker = execution.get("run_complete")
    summary = v8_report["summary"]
    legacy_completed_v8 = (
        completion_marker is None
        and len(after) == len(common) == 4
        and len(v8_report.get("rows", [])) == 4
        and summary.get("tasks") == summary.get("attempted_tasks") == 4
        and execution.get("provider_run_id") == "e1b-r10-dev-v8"
        and str(execution.get("provider_ledger_path", "")).replace("\\", "/") == ".codex/e1b/r10-v8/provider_calls.jsonl"
        and execution.get("evidence_protocol") == "declared-seed-read-v7-coverage-state-transition"
        and execution.get("test_outcomes_opened") == 0
    )
    run_complete = completion_marker is True or legacy_completed_v8
    row_schema_valid = all(
        row.get("result_schema") == RESULT_SCHEMA and row.get("transition_schema") == TRANSITION_SCHEMA
        for row in after.values()
    )
    gate_artifacts_valid = all(
        _row_gate_artifacts_valid(row) for row in after.values()
    )
    transitions = []
    for task_id in common:
        old, new = before[task_id], after[task_id]
        transitions.append(
            {
                "instance_id": task_id,
                "v7_resolved": bool(old.get("resolved")),
                "v8_resolved": bool(new.get("resolved")),
                "resolved_transition": f"{int(bool(old.get('resolved')))}->{int(bool(new.get('resolved')))}",
                "failure": new.get("failure"),
                "proposal_transition_complete": new.get("proposal_transition", {}).get("transition_witness_complete"),
                "final_transition_complete": new.get("final_transition", {}).get("transition_witness_complete"),
            }
        )
    ledger_tokens = sum(int(row.get("total_tokens", 0)) for row in completed)
    row_model_calls = sum(int(row.get("model_calls", 0)) for row in after.values())
    protocol_valid = (
        len(common) == summary.get("tasks") == 4
        and v8_report.get("result_schema") == RESULT_SCHEMA
        and execution.get("transition_schema") == TRANSITION_SCHEMA
        and execution.get("contract_coverage_enforced") is True
        and execution.get("state_transition_enforced") is True
        and execution.get("test_outcomes_opened") == 0
        and run_complete
        and row_schema_valid
        and gate_artifacts_valid
        and summary.get("model_failures") == 0
        and summary.get("budget_exhaustions") == 0
        and row_model_calls == len(started) == len(completed) == summary.get("total_model_calls")
        and ledger_tokens == summary.get("total_tokens")
    )
    regressions = [row["instance_id"] for row in transitions if row["v7_resolved"] and not row["v8_resolved"]]
    all_resolved = bool(common) and all(row["v8_resolved"] for row in transitions)
    return {
        "protocol": "e1b-dev-v8-audit-v1",
        "result_schema": RESULT_SCHEMA,
        "transition_schema": TRANSITION_SCHEMA,
        "protocol_valid": protocol_valid,
        "run_complete": run_complete,
        "completion_evidence": "explicit" if completion_marker is True else "legacy-v8-identity-and-4-row" if legacy_completed_v8 else "missing",
        "freeze_ready": protocol_valid and all_resolved and not regressions,
        "status": "freeze_candidate" if protocol_valid and all_resolved and not regressions else "valid_regressed_dev" if protocol_valid and regressions else "valid_partial_dev" if protocol_valid else "invalid_dev",
        "improved_from_v7": [row["instance_id"] for row in transitions if row["resolved_transition"] == "0->1"],
        "regressed_from_v7": regressions,
        "remaining_unresolved": [row["instance_id"] for row in transitions if not row["v8_resolved"]],
        "transition_gate_failures": [row["instance_id"] for row in transitions if row["failure"] == "state_transition_failure"],
        "transitions": transitions,
        "claim_boundary": "Repeated four-task DEV evidence only; no held-out outcome opened.",
    }


def main():
    if not V8.exists() or not LEDGER.exists():
        raise FileNotFoundError("v8 live artifacts do not exist; audit unavailable before an authorized live run")
    ledger_rows = [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]
    report = audit(json.loads(V7.read_text(encoding="utf-8")), json.loads(V8.read_text(encoding="utf-8")), ledger_rows)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
