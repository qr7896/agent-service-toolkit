import hashlib

from evals.e1c_evaluation_2_counterfactual_contract import compile_pair


def fixture(tmp_path):
    code = "def api(labels):\n    if len(labels) != 3:\n        raise ValueError('shape')\n    return labels\n"
    (tmp_path / "core.py").write_bytes(code.encode())
    return {"candidate_paths": ["core.py"], "windows": [{"path": "core.py", "source_sha256": hashlib.sha256(code.encode()).hexdigest()}]}


def test_one_representation_change_preserves_target_and_values(tmp_path):
    frozen = fixture(tmp_path)
    payload = {"setup_source": "import numpy as np\nlabels = np.array(['a', 'b', 'c'])",
               "control_action": "api(labels=['x'])", "target_action": "api(labels=labels)",
               "assertion": "", "oracle": "call_completes"}
    compiled, proof = compile_pair(payload, frozen, tmp_path)
    assert compiled["control_action"] == "api(labels=['a', 'b', 'c'])"
    assert compiled["target_action"] == payload["target_action"] and compiled["oracle"] == payload["oracle"]
    assert proof["status"] == "confounded_container_values" and proof["literal_length"] == 3
    assert proof["source_guards"][0]["predicate"] == "len(labels) != 3"
    assert not proof["preconditions_verified"] and not proof["semantic_equivalence_proven"]


def test_multiple_changed_factors_and_shadowed_array_are_unproven(tmp_path):
    frozen = fixture(tmp_path)
    payload = {"setup_source": "import numpy as np\nlabels = np.array(['a', 'b', 'c'])",
               "control_action": "api(labels=['x'], depth=1)", "target_action": "api(labels=labels, depth=2)", "assertion": ""}
    assert not compile_pair(payload, frozen, tmp_path)[1]["compiled"]
    payload.update({"control_action": "api(labels=['x'])", "target_action": "api(labels=labels)",
                    "setup_source": "import numpy as np\nnp = custom\nlabels = np.array(['a'])"})
    assert not compile_pair(payload, frozen, tmp_path)[1]["compiled"]


def test_new_parameter_support_is_not_misclassified_as_bad_fixture(tmp_path):
    frozen = fixture(tmp_path)
    payload = {"setup_source": "", "control_action": "Engine().run()", "target_action": "Engine(new_option=True).run()", "assertion": ""}
    assert not compile_pair(payload, frozen, tmp_path)[1]["compiled"]


def test_mutated_literal_binding_is_not_assumed_to_keep_original_values(tmp_path):
    frozen = fixture(tmp_path)
    for mutation in ("labels[0] = 'changed'", "labels.sort()", "custom(labels)", "np.array = custom"):
        payload = {"setup_source": "import numpy as np\nlabels = np.array(['a','b','c'])\n" + mutation,
                   "control_action": "api(labels=['x'])", "target_action": "api(labels=labels)", "assertion": ""}
        assert not compile_pair(payload, frozen, tmp_path)[1]["compiled"]
