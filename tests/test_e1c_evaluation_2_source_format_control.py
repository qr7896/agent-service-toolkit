import hashlib

import pytest

from evals.e1c_evaluation_2_source_format_control import derive_format_control


def context(tmp_path):
    source = "import datetime as dt\ndef parser(value):\n    return dt.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')\n"
    (tmp_path / "core.py").write_bytes(source.encode())
    return {"candidate_paths": ["core.py"], "windows": [{"path": "core.py", "source_sha256": hashlib.sha256(source.encode()).hexdigest()}]}


def payload():
    return {"oracle": "call_completes", "setup_source": "date = '2024-02-03T04:05:06.000Z'", "assertion": "",
            "issue_quote": "valid datetime", "expected_quote": "should complete",
            "control_action": "api({'date': '2024-02-03T04:05:06.000+00:00'})", "target_action": "api({'date': date})"}


def test_source_format_changes_only_control_not_reported_input_or_expected_behavior(tmp_path):
    original = payload()
    result, proof = derive_format_control(original, context(tmp_path), tmp_path)
    assert result["control_action"] == "api({'date': '2024-02-03T04:05:06.000000'})"
    assert all(result[k] == original[k] for k in original if k != "control_action")
    assert proof["compiled"] and proof["source_line"] == 3
    assert not proof["semantic_equivalence_proven"] and not proof["target_format_binding_proven"]
    assert proof["timezone_or_representation_may_differ"]


@pytest.mark.parametrize("change", [{"oracle": "value_relation"}, {"setup_source": "date = 'unknown'"},
                                    {"setup_source": "date = '2024-02-03T04:05:06.000Z'\ndate = custom"},
                                    {"setup_source": "date = '2024-02-03T04:05:06.000Z'\nglobals()['date'] = custom"},
                                    {"target_action": "api({'a': date, 'b': date})"},
                                    {"target_action": "api(transform(date))"}])
def test_unknown_multiple_or_computed_inputs_do_not_get_guessed_controls(tmp_path, change):
    original = {**payload(), **change}
    result, proof = derive_format_control(original, context(tmp_path), tmp_path)
    assert result == original and not proof["compiled"]


def test_unrelated_receiver_is_not_a_stdlib_format_proof(tmp_path):
    frozen = context(tmp_path)
    source = "import custom as dt\ndef parser(value):\n    return dt.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')\n"
    (tmp_path / "core.py").write_bytes(source.encode())
    frozen["windows"][0]["source_sha256"] = hashlib.sha256(source.encode()).hexdigest()
    assert not derive_format_control(payload(), frozen, tmp_path)[1]["compiled"]
