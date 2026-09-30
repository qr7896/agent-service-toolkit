from evals.e1c_strict_successor_gate import evaluate

REPLAY = {
    "provider_calls": 0,
    "consensus_candidate_task_count": 6,
    "minimum_consensus_family_support_per_task": 2,
    "total_consensus_family_support": 17,
    "rows": [{"instance_id": str(i)} for i in range(6)],
}


def preflight(**overrides):
    value = {
        "schema": "e1c-strict-successor-scenario-preflight-v1",
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
        "command": ["docker", "run", "--network", "none"],
        "stdout_sha256": "b" * 64,
        "stderr_sha256": "c" * 64,
    }
    value.update(overrides)
    return value


def test_gate_passes_only_with_real_preflighted_gain():
    value = evaluate(REPLAY, [preflight()], leakage_forbidden_hits=0)
    assert value["gate_passed"] is True
    assert value["valid_promoted_preflight_count"] == 1


def test_no_preflight_gain_keeps_gate_closed():
    assert evaluate(REPLAY, [], leakage_forbidden_hits=0)["gate_passed"] is False


def test_fail_closed_preflight_does_not_count_as_gain():
    assert evaluate(REPLAY, [preflight(execution_ready=False, returncode=1)], leakage_forbidden_hits=0)["gate_passed"] is False


def test_incomplete_provenance_keeps_gate_closed():
    assert evaluate(REPLAY, [preflight(command=[])], leakage_forbidden_hits=0)["gate_passed"] is False


def test_leakage_or_provider_call_keeps_gate_closed():
    assert evaluate(REPLAY, [preflight()], leakage_forbidden_hits=1)["gate_passed"] is False
    replay = dict(REPLAY, provider_calls=1)
    assert evaluate(replay, [preflight()], leakage_forbidden_hits=0)["gate_passed"] is False


def test_regression_in_old_dev_metrics_keeps_gate_closed():
    assert evaluate(dict(REPLAY, consensus_candidate_task_count=5), [preflight()], leakage_forbidden_hits=0)["gate_passed"] is False
    assert evaluate(dict(REPLAY, minimum_consensus_family_support_per_task=1), [preflight()], leakage_forbidden_hits=0)["gate_passed"] is False
    assert evaluate(dict(REPLAY, total_consensus_family_support=16), [preflight()], leakage_forbidden_hits=0)["gate_passed"] is False
