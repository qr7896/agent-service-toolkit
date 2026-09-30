from evals.e1b_semantic_evidence_ir_v10 import Evidence, Obligation, manifest_sha256, typed, verify


def test_combined_coverage_direct_and_helper_pass():
    obligations = [
        Obligation("coverage:a", "coverage", participant="src/a.py"),
        Obligation("state:pending", "identity", source=typed("pending")),
        Obligation("state:failed", "change", source=typed("failed"), target=typed("error")),
    ]
    evidence = [
        Evidence("c", "coverage", "support", participant="src/a.py", path="src/a.py", reason="participant_written"),
        Evidence("d", "identity", "support", source=typed("pending"), path="src/a.py", function="f", construct="if"),
        Evidence("h", "change", "support", source=typed("failed"), target=typed("error"), path="src/a.py", function="normalize", construct="helper_summary", depth=1),
    ]
    assert verify(obligations, evidence)["decision"] == "pass"


def test_contradiction_is_distinct_from_missing_evidence():
    obligation = [Obligation("x", "change", source=typed("failed"), target=typed("error"))]
    wrong = [Evidence("e", "change", "support", source=typed("failed"), target=typed("completed"), path="x.py", construct="if")]
    assert verify(obligation, wrong)["dispositions"][0]["disposition"] == "contradicted"
    assert verify(obligation, [])["dispositions"][0]["disposition"] == "unsupported"


def test_effect_risk_contradicts():
    obligation = [Obligation("x", "identity", source=typed("pending"))]
    evidence = [Evidence("e", "identity", "support", source=typed("pending"), effect_risk=True, path="x.py", construct="if")]
    assert verify(obligation, evidence)["dispositions"][0]["disposition"] == "contradicted"


def test_duplicate_support_is_ambiguous():
    obligation = [Obligation("x", "identity", source=typed("pending"))]
    evidence = [
        Evidence("a", "identity", "support", source=typed("pending"), path="x.py", function="f", construct="if"),
        Evidence("b", "identity", "support", source=typed("pending"), path="y.py", function="g", construct="if"),
    ]
    assert verify(obligation, evidence)["dispositions"][0]["disposition"] == "ambiguous"


def test_provenance_collision_is_ambiguous():
    obligation = [Obligation("x", "identity", source=typed("pending"))]
    evidence = [
        Evidence("a", "identity", "support", source=typed("pending"), path="x.py", function="f", construct="if"),
        Evidence("b", "identity", "support", source=typed("pending"), path="x.py", function="f", construct="if"),
    ]
    assert verify(obligation, evidence)["dispositions"][0]["disposition"] == "ambiguous"


def test_bool_int_are_distinct_in_ir():
    obligation = [Obligation("x", "change", source=typed(False), target=typed(True))]
    evidence = [Evidence("e", "change", "support", source=typed(0), target=typed(1), path="x.py", construct="if")]
    assert verify(obligation, evidence)["decision"] == "fail_closed"


def test_manifest_is_deterministic_for_sorted_input():
    rows = [Obligation("a", "identity", source=typed("x")), Obligation("b", "change", source=typed("y"))]
    assert manifest_sha256(rows) == manifest_sha256(list(rows))
