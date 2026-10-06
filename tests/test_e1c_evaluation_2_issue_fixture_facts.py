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
                                  "import os\nos.system('echo nope')", "eval('1+1')", "x = (api() == 991)",
                                  "import numpy as np\nnp.testing.assert_equal(api(x), 991)",
                                  "from numpy.testing import assert_equal as check\ncheck(api(x), 991)"])
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


def test_declaration_only_fixture_class_has_no_executable_method_body():
    text = "Data loading should work.\n```python\nfrom package import Schema, Field\nclass Record(Schema):\n    value = Field(required=True)\nRecord().load({'value': 'item'})\n```"
    result = extract_facts(text)
    assert result["blocks"][0]["facts"][1]["kind"] == "fixture_class"
    assert result["blocks"][0]["facts"][1]["fields"][0]["name"] == "value"


def test_doctest_only_keeps_prompt_inputs_never_displayed_answers():
    text = "Inputs should work.\n```python\n>>> x = [1, 2]\n>>> api(x)\n991\n```"
    result = extract_facts(text)
    assert "991" not in json.dumps(result["blocks"])
    assert result["blocks"][0]["prompt_input_lines"] == [1, 2]
    assert not result["blocks"][0]["output_lines_preserved"]


def test_sliced_fixture_and_assigned_terminal_method_are_preserved():
    text = "Fit should work.\n```python\nimport numpy as np\nfrom package import Estimator\nX = np.random.binomial(1, 0.5, size=(8, 3))\ny = X[:, [0, 0]].copy()\nest = Estimator().fit(X, y)\nprint(est.score_)\n```"
    result = extract_facts(text)
    assert result["blocks"][0]["facts"][3]["value"]["callee"]["owner"]["kind"] == "selection"
    assert result["blocks"][0]["terminal_call"]["callee"]["name"] == "fit"
