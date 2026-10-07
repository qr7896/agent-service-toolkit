import pytest

from evals.e1c_evaluation_2_api_obligation import (
    argument_provenance,
    obligations,
    verify_entrypoint,
)


def context(tmp_path, owner="Engine", parameter="option"):
    (tmp_path / "core.py").write_text(f"class {owner}:\n    def __init__(self, count=1): pass\n", encoding="utf-8")
    return {"issue": f"Please expose `{parameter}` in `{owner}.__init__()`, default False.", "windows": []}


@pytest.mark.parametrize("owner,parameter", [("Engine", "option"), ("Client", "cache_enabled"), ("Widget", "width")])
def test_different_API_names_are_data_not_task_rules(tmp_path, owner, parameter):
    frozen = context(tmp_path, owner, parameter)
    p = {"setup_source": f"from core import {owner} as Alias\ne = Alias()", "target_action": f"e.{parameter} = True"}
    rejected = verify_entrypoint(p, frozen, tmp_path)
    assert rejected["status"] == "unfulfilled_or_unknown"
    accepted = verify_entrypoint({**p, "target_action": f"e = Alias({parameter}=True)"}, frozen, tmp_path)
    assert accepted["status"] == "fulfilled_syntactically"
    assert not accepted["rows"][0]["source_signature"]["requested_parameter_declared"]
    assert not accepted["machine_trusted"] and not accepted["code_changed"]


@pytest.mark.parametrize("setup,target", [("from core import Engine\nEngine = other", "Engine(option=True)"),
    ("from core import Engine\ndef unused():\n    return Engine(option=True)", "Engine()"),
    ("from core import Engine", "Engine(**options)"), ("from missing import Engine", "Engine(option=True)")])
def test_shadowed_dead_dynamic_or_missing_binding_is_not_verified(tmp_path, setup, target):
    result = verify_entrypoint({"setup_source": setup, "target_action": target}, context(tmp_path), tmp_path)
    assert result["status"] == "unfulfilled_or_unknown"


def test_unsupported_prose_is_unknown_not_invented_obligation():
    assert obligations("Please improve the interface in some way.") == []


def test_wrong_public_module_is_not_matched_by_class_name_alone(tmp_path):
    frozen = context(tmp_path)
    frozen["issue"] = "Please expose `option` in `other.Engine.__init__()`."
    result = verify_entrypoint({"setup_source": "from core import Engine", "target_action": "Engine(option=True)"}, frozen, tmp_path)
    assert result["status"] == "unfulfilled_or_unknown"
    assert result["rows"][0]["reason"] == "public_qualified_module_binding_unknown"


def test_synthetic_input_type_not_promoted_to_public_fact():
    p = {"setup_source": "labels = ['a', 'b']\nother = dataset['names']", "target_action": "api(labels=labels, names=other)"}
    result = argument_provenance(p, {})
    assert result["rows"][0]["static_form"] == "List" and not result["rows"][0]["reported_input_type_proven"]
    assert result["rows"][1]["static_form"] == "unknown_without_runtime_observation"
    frozen = {"public_fixture_facts": [{"facts": [{"kind": "fixture_binding", "name": "labels", "value": {"kind": "list", "items": [{"kind": "literal", "value": "a"}, {"kind": "literal", "value": "b"}]}}]}]}
    assert argument_provenance(p, frozen)["rows"][0]["provenance"] == "public_binding_exact_match"
