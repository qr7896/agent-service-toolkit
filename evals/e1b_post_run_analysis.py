import math

from evals.e1b_experiment_package_v10_8 import verify_package

SCHEMA_VERSION = "e1b-task-outcome-v1"
OUTCOME_FIELDS = {
    "schema_version", "run_id", "task_id", "arm_id", "attempted", "resolved",
    "f2p_passed", "f2p_total", "p2p_passed", "p2p_total", "provider_status",
    "provider_calls", "input_tokens", "output_tokens", "total_tokens", "wall_time_ms",
    "retrieval_actions", "structural_escalations", "files_read", "files_written",
    "forbidden_source_accesses", "safety_events", "oracle_editable", "target_coverage",
    "failure_category",
}
PROVIDER_STATUSES = {"completed", "failed", "not_called"}
FAILURE_CATEGORIES = {
    "none", "retrieval_failure", "evidence_sufficiency_failure",
    "structural_escalation_failure", "verification_failure",
    "editor_reasoning_failure", "patch_application_failure", "regression_failure",
    "provider_infrastructure_failure", "candidate_assertion_failure",
    "candidate_exception", "candidate_timeout", "grader_bootstrap_timeout", "safety_block",
}
COUNT_FIELDS = {
    "f2p_passed", "f2p_total", "p2p_passed", "p2p_total", "provider_calls",
    "input_tokens", "output_tokens", "total_tokens", "wall_time_ms",
    "retrieval_actions", "structural_escalations", "files_read", "files_written",
    "forbidden_source_accesses", "safety_events",
}


def attribute_verification_failure(*, timed_out=False, tests_started=False, assertion_failed=False, candidate_exception=False):
    if timed_out:
        return "candidate_timeout" if tests_started else "grader_bootstrap_timeout"
    if assertion_failed:
        return "candidate_assertion_failure"
    if candidate_exception:
        return "candidate_exception"
    return "verification_failure"


def _wilson(successes, total):
    if total == 0:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return [max(0.0, center - radius), min(1.0, center + radius)]


def _validate(package, rows):
    if not verify_package(package)["valid"]:
        raise ValueError("package_manifest_invalid")
    if not isinstance(rows, (list, tuple)):
        raise ValueError("outcomes_malformed")
    if len(rows) != package["task_count"]:
        raise ValueError("outcome_denominator_mismatch")
    expected_arm = package["frozen_identifiers"]["experiment_arm_id"]
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != OUTCOME_FIELDS:
            raise ValueError("outcome_schema_mismatch")
        if row["schema_version"] != SCHEMA_VERSION or row["run_id"] != package["run_id"]:
            raise ValueError("outcome_identity_mismatch")
        if row["arm_id"] != expected_arm:
            raise ValueError("outcome_arm_mismatch")
        if not isinstance(row["task_id"], str) or not row["task_id"] or row["task_id"] in seen:
            raise ValueError("outcome_task_id_invalid")
        seen.add(row["task_id"])
        if type(row["attempted"]) is not bool or type(row["resolved"]) is not bool:
            raise ValueError("outcome_boolean_invalid")
        if row["provider_status"] not in PROVIDER_STATUSES:
            raise ValueError("outcome_provider_status_invalid")
        if row["failure_category"] not in FAILURE_CATEGORIES:
            raise ValueError("outcome_failure_category_invalid")
        if row["resolved"] != (row["failure_category"] == "none"):
            raise ValueError("outcome_resolution_failure_mismatch")
        if any(type(row[field]) is not int or row[field] < 0 for field in COUNT_FIELDS):
            raise ValueError("outcome_count_invalid")
        if row["f2p_passed"] > row["f2p_total"] or row["p2p_passed"] > row["p2p_total"]:
            raise ValueError("outcome_test_count_invalid")
        if row["total_tokens"] != row["input_tokens"] + row["output_tokens"]:
            raise ValueError("outcome_token_reconciliation_failed")
        if row["oracle_editable"] not in (True, False, None):
            raise ValueError("outcome_oracle_invalid")
        if row["target_coverage"] is not None and (
            type(row["target_coverage"]) not in (int, float)
            or not 0 <= row["target_coverage"] <= 1
        ):
            raise ValueError("outcome_target_coverage_invalid")


def analyze(package, rows, ledger_audit):
    _validate(package, rows)
    if not isinstance(ledger_audit, dict) or ledger_audit.get("valid") is not True:
        raise ValueError("ledger_audit_invalid")
    calls = sum(row["provider_calls"] for row in rows)
    tokens = sum(row["total_tokens"] for row in rows)
    if calls != ledger_audit.get("provider_calls") or tokens != ledger_audit.get("total_tokens"):
        raise ValueError("outcome_ledger_reconciliation_failed")
    total = len(rows)
    resolved = sum(row["resolved"] for row in rows)
    failures = {category: 0 for category in sorted(FAILURE_CATEGORIES - {"none"})}
    for row in rows:
        if row["failure_category"] != "none":
            failures[row["failure_category"]] += 1
    return {
        "schema_version": "e1b-post-run-analysis-v1",
        "run_id": package["run_id"],
        "arm_id": package["frozen_identifiers"]["experiment_arm_id"],
        "admitted_tasks": total,
        "attempted_tasks": sum(row["attempted"] for row in rows),
        "resolved": resolved,
        "resolved_fraction": resolved / total,
        "resolved_wilson_95": _wilson(resolved, total),
        "f2p": [sum(row["f2p_passed"] for row in rows), sum(row["f2p_total"] for row in rows)],
        "p2p": [sum(row["p2p_passed"] for row in rows), sum(row["p2p_total"] for row in rows)],
        "provider_calls": calls,
        "input_tokens": sum(row["input_tokens"] for row in rows),
        "output_tokens": sum(row["output_tokens"] for row in rows),
        "total_tokens": tokens,
        "safety_events": sum(row["safety_events"] for row in rows),
        "forbidden_source_accesses": sum(row["forbidden_source_accesses"] for row in rows),
        "failure_taxonomy": failures,
        "claim_boundary": "complete admitted single-arm outcomes; Oracle/editability and software regression are not autonomous repair",
    }


def paired_delta(left_rows, right_rows):
    left = {row["task_id"]: row for row in left_rows}
    right = {row["task_id"]: row for row in right_rows}
    if set(left) != set(right) or not left:
        raise ValueError("paired_task_ids_mismatch")
    deltas = [int(right[key]["resolved"]) - int(left[key]["resolved"]) for key in sorted(left)]
    mean = sum(deltas) / len(deltas)
    return {
        "tasks": len(deltas),
        "right_only_resolved": deltas.count(1),
        "left_only_resolved": deltas.count(-1),
        "ties": deltas.count(0),
        "resolved_fraction_delta": mean,
    }
