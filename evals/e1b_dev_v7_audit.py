import json
from pathlib import Path

V5 = Path("evals/results/e1b_autonomous_dev_run_v5.json")
V7 = Path("evals/results/e1b_autonomous_dev_run_v7b.json")
LEDGER = Path(".codex/e1b/r10-v7b/provider_calls.jsonl")
OUT = Path("evals/results/e1b_autonomous_dev_v7b_audit.json")


def row_map(report):
    return {row["instance_id"]: row for row in report["rows"]}


def audit(v5_report, v7_report, ledger_rows):
    before = row_map(v5_report)
    after = row_map(v7_report)
    common = sorted(set(before) & set(after))
    completed = [row for row in ledger_rows if row.get("status") == "completed"]
    started = [row for row in ledger_rows if row.get("status") == "started"]
    transitions = []
    for task_id in common:
        old = before[task_id]
        new = after[task_id]
        transitions.append(
            {
                "instance_id": task_id,
                "v5_resolved": bool(old.get("resolved")),
                "v7_resolved": bool(new.get("resolved")),
                "resolved_transition": f"{int(bool(old.get('resolved')))}->{int(bool(new.get('resolved')))}",
                "coverage_failure": new.get("failure") == "contract_coverage_failure",
                "proposal_coverage_complete": new.get("proposal_coverage", {}).get("participant_coverage_complete"),
                "final_coverage_complete": new.get("final_coverage", {}).get("participant_coverage_complete"),
                "v7_f2p_all": all(new.get("fail_to_pass", {}).values()),
                "v7_p2p_all": all(new.get("pass_to_pass", {}).values()),
            }
        )
    summary = v7_report["summary"]
    execution = v7_report.get("execution", {})
    ledger_tokens = sum(int(row.get("total_tokens", 0)) for row in completed)
    protocol_valid = (
        len(common) == summary.get("tasks") == 4
        and summary.get("model_failures") == 0
        and summary.get("budget_exhaustions") == 0
        and summary.get("total_tokens", 0) <= execution.get("original_token_budget", 0)
        and execution.get("test_outcomes_opened") == 0
        and execution.get("contract_coverage_enforced") is True
        and len(started) == len(completed) == summary.get("total_model_calls")
        and ledger_tokens == summary.get("total_tokens")
    )
    regressions = [row["instance_id"] for row in transitions if row["v5_resolved"] and not row["v7_resolved"]]
    all_resolved = bool(common) and all(row["v7_resolved"] for row in transitions)
    return {
        "protocol": "e1b-dev-v7-audit-v1",
        "scope": "DEV only; original TEST and replacement held-out outcomes excluded",
        "status": "freeze_candidate" if protocol_valid and all_resolved and not regressions else "valid_regressed_dev" if protocol_valid and regressions else "valid_partial_dev" if protocol_valid else "invalid_dev",
        "protocol_valid": protocol_valid,
        "freeze_ready": protocol_valid and all_resolved and not regressions,
        "resolved_count": summary.get("resolved"),
        "total_model_calls": summary.get("total_model_calls"),
        "total_tokens": summary.get("total_tokens"),
        "ledger_completed_calls": len(completed),
        "ledger_total_tokens": ledger_tokens,
        "coverage_failure_count": sum(row["coverage_failure"] for row in transitions),
        "improved_from_v5": [row["instance_id"] for row in transitions if row["resolved_transition"] == "0->1"],
        "regressed_from_v5": regressions,
        "remaining_unresolved": [row["instance_id"] for row in transitions if not row["v7_resolved"]],
        "transitions": transitions,
        "claim_boundary": "Repeated four-task DEV evidence is protocol-development evidence only.",
        "next_gate": "Freeze only if all four DEV resolve with valid artifacts and no regression; otherwise keep held-out outcomes closed.",
    }


def main():
    if not V7.exists() or not LEDGER.exists():
        raise FileNotFoundError("v7 live artifacts do not exist; audit is intentionally unavailable before an authorized live run")
    ledger_rows = [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]
    report = audit(json.loads(V5.read_text(encoding="utf-8")), json.loads(V7.read_text(encoding="utf-8")), ledger_rows)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
