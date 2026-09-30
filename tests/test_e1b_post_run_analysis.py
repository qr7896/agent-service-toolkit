import pytest

from evals.e1b_experiment_admission_v10_7 import admit
from evals.e1b_experiment_admission_v10_7_preflight import synthetic_config
from evals.e1b_experiment_package_v10_8 import REQUIRED_ARTIFACTS, audit_ledger, build_package
from evals.e1b_post_run_analysis import analyze, attribute_verification_failure, paired_delta


def package():
    config = synthetic_config()
    config.task_metadata["task_count"] = 2
    return build_package(admit(config), config)


def outcome(pkg, task_id, resolved, **updates):
    row = {
        "schema_version": "e1b-task-outcome-v1", "run_id": pkg["run_id"],
        "task_id": task_id, "arm_id": "adaptive-acquisition", "attempted": True,
        "resolved": resolved, "f2p_passed": int(resolved), "f2p_total": 1,
        "p2p_passed": 1, "p2p_total": 1, "provider_status": "completed",
        "provider_calls": 1, "input_tokens": 8, "output_tokens": 2,
        "total_tokens": 10, "wall_time_ms": 1, "retrieval_actions": 1,
        "structural_escalations": 0, "files_read": 1, "files_written": 1,
        "forbidden_source_accesses": 0, "safety_events": 0,
        "oracle_editable": True, "target_coverage": 1.0,
        "failure_category": "none" if resolved else "editor_reasoning_failure",
    }
    row.update(updates)
    return row


def ledger_audit(pkg):
    rows = [
        {"schema_version": "e1b-provider-ledger-v1", "sequence": index + 1,
         "run_id": pkg["run_id"], "call_index": index,
         "model_id": pkg["frozen_identifiers"]["model_id"],
         "request_manifest_sha256": "2" * 64, "response_manifest_sha256": "3" * 64,
         "input_tokens": 8, "output_tokens": 2, "total_tokens": 10, "status": "completed"}
        for index in range(2)
    ]
    summary = {"run_id": pkg["run_id"], "provider_calls": 2, "total_tokens": 20,
               "task_outcome_count": 2, "forbidden_source_accesses": 0,
               "package_manifest_sha256": pkg["package_manifest_sha256"]}
    return audit_ledger(pkg, rows, summary, REQUIRED_ARTIFACTS)


def test_analysis_keeps_failure_and_oracle_separate():
    assert attribute_verification_failure(timed_out=True, tests_started=False) == "grader_bootstrap_timeout"
    assert attribute_verification_failure(timed_out=True, tests_started=True) == "candidate_timeout"
    assert attribute_verification_failure(assertion_failed=True) == "candidate_assertion_failure"
    assert attribute_verification_failure(candidate_exception=True) == "candidate_exception"

    pkg = package()
    report = analyze(pkg, [outcome(pkg, "a", True), outcome(pkg, "b", False)], ledger_audit(pkg))
    assert report["admitted_tasks"] == 2
    assert report["resolved"] == 1
    assert report["failure_taxonomy"]["editor_reasoning_failure"] == 1
    assert report["resolved_wilson_95"][0] < 0.5 < report["resolved_wilson_95"][1]


def test_missing_outcome_and_ledger_drift_fail_closed():
    pkg = package()
    with pytest.raises(ValueError, match="outcome_denominator_mismatch"):
        analyze(pkg, [outcome(pkg, "a", True)], ledger_audit(pkg))
    bad = ledger_audit(pkg) | {"total_tokens": 19}
    with pytest.raises(ValueError, match="outcome_ledger_reconciliation_failed"):
        analyze(pkg, [outcome(pkg, "a", True), outcome(pkg, "b", False)], bad)


def test_resolution_cannot_be_inferred_from_oracle_editability():
    pkg = package()
    bad = outcome(pkg, "a", False, failure_category="none", oracle_editable=True)
    with pytest.raises(ValueError, match="outcome_resolution_failure_mismatch"):
        analyze(pkg, [bad, outcome(pkg, "b", False)], ledger_audit(pkg))


def test_paired_delta_requires_exact_task_ids():
    pkg = package()
    left = [outcome(pkg, "a", False), outcome(pkg, "b", True)]
    right = [outcome(pkg, "a", True), outcome(pkg, "b", True)]
    assert paired_delta(left, right) == {
        "tasks": 2, "right_only_resolved": 1, "left_only_resolved": 0,
        "ties": 1, "resolved_fraction_delta": 0.5,
    }
    with pytest.raises(ValueError, match="paired_task_ids_mismatch"):
        paired_delta(left, right[:1])
