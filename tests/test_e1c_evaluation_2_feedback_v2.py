import pytest

from evals.e1c_evaluation_2_feedback_v2 import _prompt, _source


def test_feedback_prompt_and_fenced_response_are_bounded():
    frozen = {"issue": "Public API must return the requested result", "windows": []}
    prompt = _prompt(frozen, "assert False")
    assert "exit_0_no_prepatch_failure" in prompt
    assert "reference patches" not in prompt
    assert _source('```json\n{"source":"assert True"}\n```') == "assert True"
    with pytest.raises(ValueError, match="one Python source field"):
        _source('{"abstain_reason":"insufficient evidence"}')
