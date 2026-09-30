from evals.e1c_strict_successor_setup_closure_gate import evaluate

ANALYSIS = {
    "provider_calls": 0,
    "task_count": 30,
    "behavioral_closed_candidate_count": 3,
    "behavioral_closed_repo_count": 2,
}
V25 = {
    "consensus_candidate_task_count": 6,
    "minimum_consensus_family_support_per_task": 2,
    "total_consensus_family_support": 17,
}
DJANGO_NEG = {"execution_ready": False}


def preflight(**overrides):
    value = {
        "provider_calls": 0,
        "execution_ready": True,
        "exact_base_identity": True,
        "immutable_image_identity": True,
        "network_disabled": True,
        "executed": True,
        "returncode": 0,
        "observable": "scenario_exit_code == 0",
        "expected_base_commit": "a" * 40,
        "observed_base_commit": "a" * 40,
    }
    value.update(overrides)
    return value


def test_gate_passes_with_predeclared_static_and_real_gain():
    result = evaluate(ANALYSIS, [preflight()], django11734_preflight=DJANGO_NEG, v25_replay=V25)
    assert result["gate_passed"] is True
    assert result["valid_promoted_preflight_count"] == 1


def test_no_real_preflight_gain_keeps_gate_closed():
    assert evaluate(ANALYSIS, [], django11734_preflight=DJANGO_NEG, v25_replay=V25)["gate_passed"] is False


def test_static_candidate_or_repo_shortfall_keeps_gate_closed():
    assert evaluate(dict(ANALYSIS, behavioral_closed_candidate_count=2), [preflight()], django11734_preflight=DJANGO_NEG, v25_replay=V25)["gate_passed"] is False
    assert evaluate(dict(ANALYSIS, behavioral_closed_repo_count=1), [preflight()], django11734_preflight=DJANGO_NEG, v25_replay=V25)["gate_passed"] is False


def test_django_negative_must_remain_fail_closed():
    assert evaluate(ANALYSIS, [preflight()], django11734_preflight={"execution_ready": True}, v25_replay=V25)["gate_passed"] is False


def test_leakage_task_specific_or_forbidden_access_keeps_gate_closed():
    assert evaluate(ANALYSIS, [preflight()], django11734_preflight=DJANGO_NEG, v25_replay=V25, leakage_forbidden_hits=1)["gate_passed"] is False
    assert evaluate(ANALYSIS, [preflight()], django11734_preflight=DJANGO_NEG, v25_replay=V25, task_specific_rule_count=1)["gate_passed"] is False
    assert evaluate(ANALYSIS, [preflight()], django11734_preflight=DJANGO_NEG, v25_replay=V25, forbidden_setup_access_count=1)["gate_passed"] is False


def test_v25_invariant_regression_keeps_gate_closed():
    assert evaluate(ANALYSIS, [preflight()], django11734_preflight=DJANGO_NEG, v25_replay=dict(V25, total_consensus_family_support=16))["gate_passed"] is False
