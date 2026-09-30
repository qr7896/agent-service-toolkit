import pytest

from evals.e1c_evaluation_2_dev_batch_v2 import _prompt, _quote


def test_public_issue_prompt_has_no_executable_placeholder():
    frozen = {"issue": "Make the public API return the requested value", "windows": []}
    prompt = _prompt(frozen)
    assert "complete executable Python source code" in prompt
    assert '"source":"Python probe"' not in prompt
    assert _quote(frozen) == frozen["issue"]


def test_public_quote_rejects_empty_title():
    with pytest.raises(ValueError, match="no public issue title"):
        _quote({"issue": "short"})
