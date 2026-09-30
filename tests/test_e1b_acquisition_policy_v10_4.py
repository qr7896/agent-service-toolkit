import pytest

from evals.e1b_acquisition_counterfactual_v10_4 import counterfactual_replay
from evals.e1b_acquisition_policy_interface_v10_4 import (
    DeterministicBaselinePolicy,
    PolicyContext,
    action_set_manifest,
    audit_feature_leakage,
    dominance_report,
    runtime_features,
)
from evals.e1b_evidence_acquisition_v10_3 import choose_action
from evals.e1b_semantic_evidence_ir_v10 import Evidence, Obligation, typed, verify


def test_interface_parity_with_v10_3():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    verification = verify(obligations, [])
    context = PolicyContext((), 0)
    assert DeterministicBaselinePolicy().select(obligations, verification, context) == choose_action(obligations, verification, [], 0)


def test_runtime_features_have_no_gold_leakage():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    features = runtime_features(obligations, verify(obligations, []), PolicyContext((), 0))
    assert features
    assert audit_feature_leakage(features) == {"runtime_gold_leakage": []}


def test_leakage_audit_rejects_forbidden_fields():
    with pytest.raises(ValueError):
        audit_feature_leakage([{"action": "x", "grader_outcome": 1}])


def test_leakage_audit_recurses_and_checks_provenance_labels():
    with pytest.raises(ValueError):
        audit_feature_leakage([{"safe": {"nested": [{"expected_patch": "x"}]}}])
    with pytest.raises(ValueError):
        audit_feature_leakage([{"provenance": "gold-grader"}])
    assert audit_feature_leakage([{"note": "benign test string"}]) == {"runtime_gold_leakage": []}


def test_tie_break_and_admissibility_are_deterministic():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    result = DeterministicBaselinePolicy().select(obligations, verify(obligations, []), PolicyContext((), 0))
    assert result["action"] == "lexical"


def test_features_mark_irrelevant_coverage_action():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    features = runtime_features(obligations, verify(obligations, []), PolicyContext((), 0))
    coverage = next(row for row in features if row["action"] == "coverage_check")
    assert coverage["compatible"] is False


def test_counterfactual_replay_arms_are_isolated_and_stable():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    support = Evidence("e", "identity", "support", source=typed("pending"), path="x.py", construct="if")
    results = {"direct_ast": [support]}
    a = counterfactual_replay(obligations, results)
    b = counterfactual_replay(obligations, results)
    assert a == b
    direct = next(row for row in a["arms"] if row["first_action"] == "direct_ast")
    lexical = next(row for row in a["arms"] if row["first_action"] == "lexical")
    assert direct["protocol_cost"] == 2
    assert lexical["protocol_cost"] >= 3
    assert "repair_success" not in a["metrics"]


def test_dominance_report_does_not_mutate_action_set():
    before = action_set_manifest()
    report = dominance_report()
    after = action_set_manifest()
    assert before == after
    assert isinstance(report, list)


def test_action_set_hash_is_stable():
    assert action_set_manifest() == action_set_manifest()
