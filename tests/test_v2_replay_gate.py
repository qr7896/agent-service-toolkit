from evals.v2_replay_gate import SourceProvenance, replay_eligibility

def valid(n=200):
    return {"records":n,"minimum_records":200,"ready_for_replay":n>=200,"errors":[]}

def test_derived_uniform_never_ips_ready():
    g=replay_eligibility(valid(),[SourceProvenance("derived_offline","derived_uniform")])
    assert g["supervised_replay_ready"] is True and g["ips_ready"] is False

def test_deterministic_plumbing_never_ips_ready():
    assert replay_eligibility(valid(),[SourceProvenance("deterministic_runtime","plumbing_uniform")])["ips_ready"] is False

def test_empirical_logged_requires_behavior_policy():
    assert replay_eligibility(valid(),[SourceProvenance("empirical_logged","logged_behavior")])["ips_ready"] is False
    assert replay_eligibility(valid(),[SourceProvenance("empirical_logged","logged_behavior","epsilon-v1")])["ips_ready"] is True

def test_sample_gate_blocks_all_replay():
    g=replay_eligibility(valid(199),[SourceProvenance("empirical_logged","logged_behavior","p")])
    assert not g["generic_replay_ready"] and not g["supervised_replay_ready"] and not g["ips_ready"]
