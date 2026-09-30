import json
from pathlib import Path

V4 = Path("evals/results/e1b_autonomous_dev_run_v4.json")
V5 = Path("evals/results/e1b_autonomous_dev_run_v5.json")
LEDGER = Path(".codex/e1b/r10-v5/provider_calls.jsonl")
OUT = Path("evals/results/e1b_autonomous_dev_v5_audit.json")


def row_map(report):
    return {row["instance_id"]: row for row in report["rows"]}


def audit(v4_report, v5_report, ledger_rows):
    before = row_map(v4_report)
    after = row_map(v5_report)
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
                "v4_resolved": bool(old.get("resolved")),
                "v5_resolved": bool(new.get("resolved")),
                "resolved_transition": f"{int(bool(old.get('resolved')))}->{int(bool(new.get('resolved')))}",
                "same_final_patch_as_v4": old.get("patch_sha256") == new.get("patch_sha256"),
                "review_changed_patch": bool(new.get("review_changed_patch")),
                "v5_f2p_all": all(new.get("fail_to_pass", {}).values()),
                "v5_p2p_all": all(new.get("pass_to_pass", {}).values()),
            }
        )
    summary = v5_report["summary"]
    execution = v5_report.get("execution", {})
    ledger_tokens = sum(int(row.get("total_tokens", 0)) for row in completed)
    protocol_valid = (
        len(common) == summary.get("tasks") == 4
        and summary.get("parse_failures") == 0
        and summary.get("model_failures") == 0
        and summary.get("budget_exhaustions") == 0
        and summary.get("total_tokens", 0) <= execution.get("original_token_budget", 0)
        and execution.get("test_outcomes_opened") == 0
        and len(started) == len(completed) == summary.get("total_model_calls") == 8
        and ledger_tokens == summary.get("total_tokens")
    )
    all_resolved = bool(common) and all(row["v5_resolved"] for row in transitions)
    regressions = [
        row["instance_id"]
        for row in transitions
        if row["v4_resolved"] and not row["v5_resolved"]
    ]
    return {
        "protocol": "e1b-dev-v5-audit-v1",
        "scope": "DEV only; original sealed TEST outcomes unopened by the experiment",
        "status": "valid_partial_dev" if protocol_valid and not all_resolved else "freeze_candidate" if protocol_valid else "invalid_dev",
        "protocol_valid": protocol_valid,
        "freeze_ready": protocol_valid and all_resolved and not regressions,
        "resolved_count": summary.get("resolved"),
        "total_model_calls": summary.get("total_model_calls"),
        "total_tokens": summary.get("total_tokens"),
        "ledger_completed_calls": len(completed),
        "ledger_total_tokens": ledger_tokens,
        "review_changed_count": sum(row["review_changed_patch"] for row in transitions),
        "improved_from_v4": [row["instance_id"] for row in transitions if row["resolved_transition"] == "0->1"],
        "regressed_from_v4": regressions,
        "remaining_unresolved": [row["instance_id"] for row in transitions if not row["v5_resolved"]],
        "transitions": transitions,
        "claim_boundary": "This four-task repeatedly used DEV set is protocol-development evidence, not a population repair-rate estimate.",
        "next_gate": "Do not freeze or open held-out outcomes unless all four DEV tasks resolve without regression and the artifact audit remains valid.",
    }


def main():
    ledger_rows = [
        json.loads(line)
        for line in LEDGER.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    report = audit(
        json.loads(V4.read_text(encoding="utf-8")),
        json.loads(V5.read_text(encoding="utf-8")),
        ledger_rows,
    )
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
