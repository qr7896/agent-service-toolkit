import pytest

from evals.e1b_run_dev_live_v8 import (
    LEDGER_PATH,
    RESULT_PATH,
    CoverageGateFailure,
    TransitionGateFailure,
    preflight,
    verify_candidate,
)


def payload(statement, setup_files):
    return {"problem_statement": statement, "setup_files": setup_files}


def test_zero_transition_obligations_do_not_reject_complete_patch():
    coverage, transition = verify_candidate(
        payload("Update the configured budget.", ["src/budget.py"]),
        {"src/budget.py": "BUDGET = 3"},
    )
    assert coverage["participant_coverage_complete"] is True
    assert transition["obligations"] == []
    assert transition["transition_witness_complete"] is True


def test_verify_candidate_checks_coverage_before_transition():
    with pytest.raises(CoverageGateFailure, match="contract coverage incomplete"):
        verify_candidate(
            payload("错误映射为 failed，保持 pending 不变。", ["src/status.py", "src/adapter.py"]),
            {"src/status.py": "if status == 'pending': return status\nreturn 'failed'"},
        )


def test_transition_gate_rejects_missing_identity_witness_after_coverage_passes():
    with pytest.raises(TransitionGateFailure, match="state-transition witness incomplete"):
        verify_candidate(
            payload("迁移 version 1，并保持 version 2 不变。", ["src/migrate.py"]),
            {"src/migrate.py": "if version == 1:\n    return migrate(data)"},
        )


def test_failure_types_are_distinct():
    assert issubclass(CoverageGateFailure, ValueError)
    assert issubclass(TransitionGateFailure, ValueError)
    assert CoverageGateFailure is not TransitionGateFailure

def test_coverage_rejection_carries_deterministic_audit():
    with pytest.raises(CoverageGateFailure) as caught:
        verify_candidate(
            payload("Update both participants.", ["src/a.py", "src/b.py"]),
            {"src/a.py": "VALUE = 1"},
        )
    assert caught.value.audit["participant_coverage_complete"] is False
    assert caught.value.audit["missing_required_participants"] == ["src/b.py"]


def test_transition_rejection_carries_deterministic_audit():
    with pytest.raises(TransitionGateFailure) as caught:
        verify_candidate(
            payload("迁移 version 1，并保持 version 2 不变。", ["src/migrate.py"]),
            {"src/migrate.py": "if version == 1:\n    return migrate(data)"},
        )
    assert caught.value.audit["transition_witness_complete"] is False
    assert any(item["mode"] == "identity" for item in caught.value.audit["missing_obligations"])



def test_live_preflight_is_zero_call_fresh_and_reserve_fit():
    report = preflight()
    assert report["provider_calls"] == 0
    assert report["live_authorized"] is False
    assert report["result_schema"] == "e1b-r10-v8-result-v1"
    assert report["transition_schema"] == "e1b-state-transition-v1"
    assert report["result_exists"] == RESULT_PATH.exists()
    assert report["ledger_exists"] == LEDGER_PATH.exists()
    assert report["ready"] is (not RESULT_PATH.exists() and not LEDGER_PATH.exists())
    assert all(row["proposal_reserve_fits"] and row["review_reserve_fits"] for row in report["rows"])
