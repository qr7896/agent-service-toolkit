import json
from pathlib import Path

V5 = Path("evals/results/e1b_autonomous_dev_run_v5.json")
V6 = Path("evals/results/e1b_autonomous_dev_run_v6.json")
LEDGER = Path(".codex/e1b/r10-v6/provider_calls.jsonl")
OUT = Path("evals/results/e1b_autonomous_dev_v6_audit.json")


def row_map(report):
    return {row["instance_id"]: row for row in report["rows"]}


def audit(v5_report, v6_report, ledger_rows):
    before = row_map(v5_report)
    after = row_map(v6_report)
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
                "v6_resolved": bool(new.get("resolved")),
                "resolved_transition": f"{int(bool(old.get('resolved')))}->{int(bool(new.get('resolved')))}",
                "same_final_patch_as_v5": old.get("patch_sha256") == new.get("patch_sha256"),
                "review_changed_patch": bool(new.get("review_changed_patch")),
                "v6_f2p_all": all(new.get("fail_to_pass", {}).values()),
                "v6_p2p_all": all(new.get("pass_to_pass", {}).values()),
            }
        )
    summary = v6_report["summary"]
    execution = v6_report.get("execution", {})
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
    regressions = [
        row["instance_id"]
        for row in transitions
        if row["v5_resolved"] and not row["v6_resolved"]
    ]
    all_resolved = bool(common) and all(row["v6_resolved"] for row in transitions)
    return {
        "protocol": "e1b-dev-v6-audit-v1",
        "scope": "DEV only; original sealed TEST outcomes unopened by the experiment",
        "status": "valid_regressed_dev" if protocol_valid and regressions else "valid_partial_dev" if protocol_valid and not all_resolved else "freeze_candidate" if protocol_valid else "invalid_dev",
        "protocol_valid": protocol_valid,
        "freeze_ready": protocol_valid and all_resolved and not regressions,
        "resolved_count": summary.get("resolved"),
        "total_model_calls": summary.get("total_model_calls"),
        "total_tokens": summary.get("total_tokens"),
        "ledger_completed_calls": len(completed),
        "ledger_total_tokens": ledger_tokens,
        "review_changed_count": sum(row["review_changed_patch"] for row in transitions),
        "improved_from_v5": [row["instance_id"] for row in transitions if row["resolved_transition"] == "0->1"],
        "regressed_from_v5": regressions,
        "remaining_unresolved": [row["instance_id"] for row in transitions if not row["v6_resolved"]],
        "transitions": transitions,
        "claim_boundary": "This four-task repeatedly used DEV set is protocol-development evidence, not a population repair-rate estimate.",
        "interpretation": "The deterministic contract representation did not clear the preservation failures and introduced a DEV regression, so it must not replace v5 as the freeze candidate.",
        "next_gate": "Keep v5 as the best observed DEV configuration; do not freeze or open held-out outcomes. Any further live DEV version requires new exact authorization.",
    }


def main():
    ledger_rows = [
        json.loads(line)
        for line in LEDGER.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    report = audit(
        json.loads(V5.read_text(encoding="utf-8")),
        json.loads(V6.read_text(encoding="utf-8")),
        ledger_rows,
    )
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
