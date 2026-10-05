import json

import pytest

from evals.e1c_evaluation_2_issue_fixture_facts import extract_facts


def test_fixture_dtype_preserved_without_executable_assertions():
    text = "Input should work.\n```python\nimport numpy as np\nx = np.random.choice(['left', 'right'], size=8).astype(object)\napi(x)\n```"
    result = extract_facts(text)
    block = result["blocks"][0]
    assert block["facts"][1]["value"]["callee"]["name"] == "astype"
    assert block["facts"][1]["value"]["arguments"] == [{"kind": "reference", "name": "object"}]
    assert block["terminal_call"]["callee"]["name"] == "api"
    assert not result["executed"] and not result["assertion_oracle_preserved"]


@pytest.mark.parametrize("unsafe", ["assert api(x) == 991", "expected = [991]", "import pytest\npytest.raises(ValueError)",
                                  "import os\nos.system('echo nope')", "eval('1+1')", "x = (api() == 991)"])
def test_oracle_and_capability_blocks_fail_closed(unsafe):
    text = "The input should work.\n```python\nx = [1, 2]\n" + unsafe + "\n```"
    result = extract_facts(text)
    assert result["blocks"] == []
    assert "991" not in json.dumps(result["blocks"])
    assert len(result["rejected_blocks"]) == 1


def test_terminal_observation_call_not_lost_behind_fixture_setters():
    text = "Objects are inconsistent.\n```python\nA = Anchor('A')\nB = Anchor('B')\nA.set_pos(B, 3)\nA.velocity(F)\n```"
    result = extract_facts(text)
    assert result["blocks"][0]["terminal_call"]["callee"]["name"] == "velocity"
