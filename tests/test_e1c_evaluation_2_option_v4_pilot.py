from evals.e1c_evaluation_2_option_v4_pilot import _prompt


def test_option_prompt_contains_only_public_context():
    prompt = _prompt({"issue": "Deprecate `--strict`", "windows": []})
    assert "--strict" in prompt
    assert "complete Python code" in prompt
    assert "test.patch" not in prompt
