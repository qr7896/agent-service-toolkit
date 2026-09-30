from evals.e1c_strict_successor_expected_failure_gate import evaluate


def _analysis():
    return {
        "provider_calls": 0,
        "task_count": 30,
        "exception_contract_candidate_count": 2,
        "exception_contract_repo_count": 2,
        "compile_ready_candidate_count": 2,
        "compile_ready_repo_count": 2,
    }


def _preflight(trusted=True):
    return {
        "provider_calls": 0,
        "trusted_reproducer": trusted,
        "exact_base_identity": True,
        "immutable_image_identity": True,
        "network_disabled": True,
        "executed": True,
    }


def test_gate_passes_only_with_real_trusted_reproducer():
    out = evaluate(_analysis(), [_preflight()], prior_setup_closure_gate={"gate_passed": False})
    assert out["gate_passed"] is True
    assert out["trusted_reproducer_count"] == 1


def test_gate_fails_without_trusted_reproducer_or_if_prior_negative_mutates():
    out = evaluate(_analysis(), [_preflight(False)], prior_setup_closure_gate={"gate_passed": False})
    assert out["gate_passed"] is False
    assert out["requirements"]["trusted_reproducer_gain"] is False
    mutated = evaluate(_analysis(), [_preflight()], prior_setup_closure_gate={"gate_passed": True})
    assert mutated["gate_passed"] is False
    assert mutated["requirements"]["prior_setup_closure_remains_negative"] is False
