from evals.e1c_evaluation_2_option_v5_pro import _prompt


def test_strict_standalone_probe_contract():
    prompt = _prompt({"issue": "Deprecate `--strict`", "windows": []})
    assert "at least one Python `assert`" in prompt
    assert "Never import `subprocess`" in prompt
    assert "--strict" in prompt
