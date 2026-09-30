import json
from pathlib import Path

V2 = Path("evals/results/e1b_autonomous_dev_run_v2.json")
V3 = Path("evals/results/e1b_autonomous_dev_run_v3.json")
OUT = Path("evals/results/e1b_autonomous_dev_v3_audit.json")


def row_map(report):
    return {row["instance_id"]: row for row in report["rows"]}


def audit(v2_report, v3_report):
    before = row_map(v2_report)
    after = row_map(v3_report)
    common = sorted(set(before) & set(after))
    transitions = []
    for task_id in common:
        old = before[task_id]
        new = after[task_id]
        transitions.append(
            {
                "instance_id": task_id,
                "v2_resolved": bool(old.get("resolved")),
                "v3_resolved": bool(new.get("resolved")),
                "resolved_transition": f"{int(bool(old.get('resolved')))}->{int(bool(new.get('resolved')))}",
                "review_changed_patch": bool(new.get("review_changed_patch")),
                "v3_f2p_all": all(new.get("fail_to_pass", {}).values()),
                "v3_p2p_all": all(new.get("pass_to_pass", {}).values()),
            }
        )
    summary = v3_report["summary"]
    execution = v3_report.get("execution", {})
    protocol_valid = (
        len(common) == summary.get("tasks") == 4
        and summary.get("parse_failures") == 0
        and summary.get("model_failures") == 0
        and summary.get("budget_exhaustions") == 0
        and summary.get("total_tokens", 0) <= execution.get("original_token_budget", 0)
        and execution.get("test_outcomes_opened") == 0
    )
    all_resolved = bool(common) and all(row["v3_resolved"] for row in transitions)
    return {
        "protocol": "e1b-dev-v3-audit-v1",
        "scope": "DEV only; sealed TEST outcomes unopened by the experiment",
        "status": "valid_partial_dev" if protocol_valid and not all_resolved else "review_required",
        "protocol_valid": protocol_valid,
        "freeze_ready": protocol_valid and all_resolved,
        "resolved_count": summary.get("resolved"),
        "total_model_calls": summary.get("total_model_calls"),
        "total_tokens": summary.get("total_tokens"),
        "review_changed_count": sum(row["review_changed_patch"] for row in transitions),
        "improved_from_v2": [
            row["instance_id"] for row in transitions if row["resolved_transition"] == "0->1"
        ],
        "remaining_unresolved": [
            row["instance_id"] for row in transitions if not row["v3_resolved"]
        ],
        "transitions": transitions,
        "claim_boundary": "This four-task DEV result is protocol-development evidence, not a population repair-rate estimate.",
        "next_gate": "Do not freeze. Improve edit reasoning using DEV-only failure classes, version the protocol, and validate offline before any new live run.",
    }


def main():
    report = audit(
        json.loads(V2.read_text(encoding="utf-8")),
        json.loads(V3.read_text(encoding="utf-8")),
    )
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
