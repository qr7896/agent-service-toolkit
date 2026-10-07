import pytest

from evals.e1c_evaluation_2_contrast_audit import contrast_evidence, truth_guard_evidence


def test_identical_actions_flagged_without_modifying_source():
    payload = {"control_action": " api() # normal", "target_action": "api()"}
    payload["control_action"] = payload["control_action"].lstrip()
    original = dict(payload)
    result = contrast_evidence(payload)
    assert result["identical_action_AST"] and payload == original
    assert not result["control_independence_proven"] and not result["code_executed"]


def test_different_actions_not_a_certificate():
    result = contrast_evidence({"control_action": "api(a)", "target_action": "api(b)"})
    assert not result["identical_action_AST"]
    assert not result["semantic_alignment_proven"] and not result["control_independence_proven"]


def test_plain_guard_has_implicit_protocol_not_type_or_failure_fact():
    result = truth_guard_evidence("values")
    assert result["supported"] and result["possible_protocols"] == ["__bool__", "__len__"]
    assert result["explicit_raise_not_required"] and result["runtime_type"] == "unknown"
    assert not result["exception_observed"] and result["hypothesis_not_report_fact"]


@pytest.mark.parametrize("expression", ["values is not None", "invoke()", "obj.values"])
def test_unknown_expression_not_evaluated_or_guessed(expression):
    result = truth_guard_evidence(expression)
    assert not result["supported"] and not result["possible_protocols"] and not result["code_executed"]
