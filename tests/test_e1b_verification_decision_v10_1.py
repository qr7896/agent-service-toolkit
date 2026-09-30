from evals.e1b_semantic_evidence_ir_v10 import Evidence, Obligation, typed, verify
from evals.e1b_verification_decision_v10_1 import MAX_ESCALATIONS, PRIORITY, decide


def decision(obligations, evidence, used=0):
    return decide(obligations, verify(obligations, evidence), used)


def test_all_satisfied_allows_verification_not_success():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    evidence = [Evidence("e", "identity", "support", source=typed("pending"), path="x.py", construct="if")]
    result = decision(obligations, evidence)
    assert result["action"] == "ALLOW_VERIFICATION"
    assert "not PASS or repair success" in result["claim_boundary"]


def test_contradiction_blocks_without_budget_spend():
    obligations = [Obligation("x", "change", source=typed("failed"), target=typed("error"))]
    evidence = [Evidence("e", "change", "support", source=typed("failed"), target=typed("wrong"), path="x.py", construct="if")]
    result = decision(obligations, evidence, 1)
    assert result["action"] == "BLOCK_PATCH"
    assert result["escalations_used_after"] == 1


def test_ambiguity_precedes_unsupported():
    obligations = [
        Obligation("a", "identity", source=typed("pending")),
        Obligation("b", "identity", source=typed("unknown")),
    ]
    evidence = [
        Evidence("e1", "identity", "support", source=typed("pending"), path="a.py", construct="if"),
        Evidence("e2", "identity", "support", source=typed("pending"), path="b.py", construct="if"),
    ]
    result = decision(obligations, evidence)
    assert result["dominant_disposition"] == "ambiguous"
    assert result["action"] == "STRUCTURAL_ESCALATION"


def test_unsupported_requests_more_evidence_and_spends_budget():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    result = decision(obligations, [])
    assert result["action"] == "REQUEST_MORE_EVIDENCE"
    assert result["escalations_used_after"] == 1


def test_budget_exhaustion_blocks():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    result = decision(obligations, [], MAX_ESCALATIONS)
    assert result["action"] == "BLOCK_PATCH"
    assert result["reason"] == "escalation_budget_exhausted"


def test_mixed_contradiction_has_highest_priority():
    obligations = [
        Obligation("a", "change", source=typed("failed"), target=typed("error")),
        Obligation("b", "identity", source=typed("missing")),
    ]
    evidence = [Evidence("e", "change", "support", source=typed("failed"), target=typed("wrong"), path="x.py", construct="if")]
    result = decision(obligations, evidence)
    assert result["dominant_disposition"] == "contradicted"
    assert tuple(result["priority"]) == PRIORITY


def test_sufficiency_counts_and_kind_coverage():
    obligations = [
        Obligation("c", "coverage", participant="a.py"),
        Obligation("i", "identity", source=typed("pending")),
    ]
    evidence = [Evidence("c1", "coverage", "support", participant="a.py", path="a.py")]
    result = decision(obligations, evidence)
    assert result["sufficiency"]["required"] == 2
    assert result["sufficiency"]["satisfied"] == 1
    assert result["sufficiency"]["unsupported"] == 1
    assert result["sufficiency"]["by_kind"]["coverage"] == {"required": 1, "satisfied": 1}


def test_decision_hash_is_deterministic():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    a = decision(obligations, [])
    b = decision(obligations, [])
    assert a["audit_manifest_sha256"] == b["audit_manifest_sha256"]
