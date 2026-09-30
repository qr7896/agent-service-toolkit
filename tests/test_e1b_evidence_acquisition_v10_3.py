from evals.e1b_evidence_acquisition_runtime_v10_3 import run
from evals.e1b_evidence_acquisition_v10_3 import MAX_ACQUISITION_COST, choose_action
from evals.e1b_semantic_evidence_ir_v10 import Evidence, Obligation, typed, verify


def test_cheapest_compatible_action_and_no_irrelevant_coverage():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    choice = choose_action(obligations, verify(obligations, []), [], 0)
    assert choice["action"] == "lexical"


def test_coverage_selects_coverage_check():
    obligations = [Obligation("c", "coverage", participant="a.py")]
    assert choose_action(obligations, verify(obligations, []), [], 0)["action"] == "coverage_check"


def test_failed_action_is_not_repeated():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    verification = verify(obligations, [])
    assert choose_action(obligations, verification, ["lexical"], 1)["action"] == "direct_ast"


def test_ambiguity_prefers_structural_escalation():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    evidence = [
        Evidence("a", "identity", "support", source=typed("pending"), path="a.py", construct="if"),
        Evidence("b", "identity", "support", source=typed("pending"), path="b.py", construct="if"),
    ]
    assert choose_action(obligations, verify(obligations, evidence), [], 0)["action"] == "structural_escalation"


def test_contradiction_bypasses_acquisition():
    obligations = [Obligation("x", "change", source=typed("failed"), target=typed("error"))]
    evidence = [Evidence("w", "change", "support", source=typed("failed"), target=typed("wrong"), path="x.py", construct="if")]
    assert choose_action(obligations, verify(obligations, evidence), [], 0)["action"] == "BYPASS_BLOCK"


def test_action_exhaustion():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    attempted = ["lexical", "direct_ast", "helper_summary"]
    assert choose_action(obligations, verify(obligations, []), attempted, 6)["action"] == "EXHAUSTED"


def test_cost_budget_exhaustion():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    result = choose_action(obligations, verify(obligations, []), ["lexical", "direct_ast"], MAX_ACQUISITION_COST - 1)
    assert result["action"] == "BUDGET_EXHAUSTED"


def test_runtime_eventual_resolution_and_deterministic_hash():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    support = Evidence("e", "identity", "support", source=typed("pending"), path="x.py", construct="if")
    action_results = {"direct_ast": [support]}
    a = run(obligations, action_results)
    b = run(obligations, action_results)
    assert a["attempted_actions"] == ["lexical", "direct_ast"]
    assert a["terminal_action"] == "ALLOW_VERIFICATION"
    assert a["trace_sha256"] == b["trace_sha256"]
    assert "repair_success" not in a
