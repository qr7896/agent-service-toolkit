import json
from pathlib import Path

OLD = Path("evals/results/e1b_autonomous_dev_run.json")
CURRENT = Path("evals/results/e1b_autonomous_dev_run_v2.json")
OUT = Path("evals/results/e1b_autonomous_dev_v2_audit.json")


def row_map(report):
    return {row["instance_id"]: row for row in report["rows"]}


def audit(old_report, current_report):
    old = row_map(old_report)
    current = row_map(current_report)
    common = sorted(set(old) & set(current))
    transitions = []
    for task_id in common:
        before = old[task_id]
        after = current[task_id]
        transitions.append(
            {
                "instance_id": task_id,
                "old_resolved": bool(before.get("resolved")),
                "current_resolved": bool(after.get("resolved")),
                "resolved_transition": f"{int(bool(before.get('resolved')))}->{int(bool(after.get('resolved')))}",
                "same_patch": before.get("patch_sha256") == after.get("patch_sha256"),
                "current_f2p_all": all(after.get("fail_to_pass", {}).values()),
                "current_p2p_all": all(after.get("pass_to_pass", {}).values()),
            }
        )

    current_summary = current_report["summary"]
    budget_valid = (
        current_report.get("execution", {}).get("budget_status") == "within_limit"
        and current_summary.get("budget_exhaustions") == 0
        and current_summary.get("model_failures") == 0
        and current_summary.get("parse_failures") == 0
    )
    all_resolved = bool(common) and all(row["current_resolved"] for row in transitions)
    regressed = [row["instance_id"] for row in transitions if row["resolved_transition"] == "1->0"]
    repeated_failed_patch = [
        row["instance_id"]
        for row in transitions
        if not row["current_resolved"] and row["same_patch"]
    ]
    return {
        "protocol": "e1b-dev-v2-audit-v1",
        "scope": "DEV only; sealed TEST outcomes unopened",
        "status": "valid_failed_dev" if budget_valid and not all_resolved else "review_required",
        "budget_and_call_chain_valid": budget_valid,
        "freeze_ready": budget_valid and all_resolved,
        "claim_boundary": "A valid failed DEV protocol result is diagnostic evidence, not an Autonomous Repair Rate conclusion.",
        "current_tasks": current_summary["tasks"],
        "current_resolved_count": current_summary["resolved"],
        "current_total_model_calls": current_summary["total_model_calls"],
        "current_total_tokens": current_summary["total_tokens"],
        "regressed_from_old_dev": regressed,
        "repeated_failed_patch": repeated_failed_patch,
        "transitions": transitions,
        "next_gate": "Improve the editor protocol on DEV, rerun a new version under a new artifact path, and freeze only after the DEV protocol is both budget-valid and edit-quality-ready.",
    }


def main():
    report = audit(
        json.loads(OLD.read_text(encoding="utf-8")),
        json.loads(CURRENT.read_text(encoding="utf-8")),
    )
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
