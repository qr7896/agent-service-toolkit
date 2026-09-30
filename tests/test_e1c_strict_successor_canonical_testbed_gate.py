from evals.e1c_strict_successor_canonical_testbed_gate import evaluate


def test_cti_gate_requires_cross_repo_environment_and_trusted_reproducer():
    analysis = {
        "provider_calls": 0,
        "task_count": 30,
        "compile_ready_candidate_count": 2,
        "compile_ready_repo_count": 2,
    }
    env = {
        "repo_count": 2,
        "probes": [{"available": True}, {"available": True}],
    }
    preflight = {
        "provider_calls": 0,
        "trusted_reproducer": True,
        "exact_base_identity": True,
        "immutable_image_identity": True,
        "network_disabled": True,
        "executed": True,
    }
    out = evaluate(analysis, env, [preflight], prior_efil_gate={"gate_passed": False})
    assert out["gate_passed"] is True
    env["probes"][1]["available"] = False
    assert evaluate(analysis, env, [preflight], prior_efil_gate={"gate_passed": False})["gate_passed"] is False
