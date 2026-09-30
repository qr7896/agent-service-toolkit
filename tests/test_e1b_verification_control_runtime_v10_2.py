from evals.e1b_semantic_evidence_ir_v10 import Evidence, Obligation, typed
from evals.e1b_verification_control_runtime_v10_2 import run_control_runtime


def test_unsupported_then_new_evidence_allows_verification():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    evidence = Evidence("e", "identity", "support", source=typed("pending"), path="x.py", construct="if")
    result = run_control_runtime(obligations, [[], [evidence]])
    assert [row["action"] for row in result["trace"]] == ["REQUEST_MORE_EVIDENCE", "ALLOW_VERIFICATION"]


def test_ambiguity_then_disambiguating_round_can_allow():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    unsupported = Evidence("u", "identity", "unsupported", source=typed("pending"), path="x.py", construct="dynamic")
    support = Evidence("s", "identity", "support", source=typed("pending"), path="y.py", construct="if")
    result = run_control_runtime(obligations, [[unsupported], [support]])
    assert result["trace"][0]["action"] == "REQUEST_MORE_EVIDENCE"
    assert result["terminal_action"] == "ALLOW_VERIFICATION"


def test_contradiction_blocks_immediately():
    obligations = [Obligation("x", "change", source=typed("failed"), target=typed("error"))]
    wrong = Evidence("w", "change", "support", source=typed("failed"), target=typed("wrong"), path="x.py", construct="if")
    result = run_control_runtime(obligations, [[wrong]])
    assert result["terminal_action"] == "BLOCK_PATCH"
    assert len(result["trace"]) == 1
    assert result["trace"][0]["escalations_used_after"] == 0


def test_persistent_unsupported_exhausts_budget():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    result = run_control_runtime(obligations, [[], [], []])
    assert result["terminal_action"] == "BLOCK_PATCH"
    assert result["trace"][-1]["reason"] == "escalation_budget_exhausted"


def test_max_step_guard_is_independent():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    result = run_control_runtime(obligations, [[]], max_steps=1)
    assert result["terminal_action"] == "BLOCK_PATCH"
    assert result["trace"][-1]["reason"] == "max_steps_exhausted"


def test_conflicting_duplicate_evidence_ids_are_auditable():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    a = Evidence("same", "identity", "support", source=typed("pending"), path="a.py", construct="if")
    b = Evidence("same", "change", "support", source=typed("pending"), target=typed("done"), path="b.py", construct="if")
    result = run_control_runtime(obligations, [[a, b]])
    assert result["trace"][0]["reason"] == "evidence_id_collision"
    assert result["trace"][0]["evidence_collisions"] == ["same"]


def test_bool_int_mismatch_never_allows_verification():
    obligations = [Obligation("x", "change", source=typed(False), target=typed(True))]
    evidence = Evidence("e", "change", "support", source=typed(0), target=typed(1), path="x.py", construct="if")
    result = run_control_runtime(obligations, [[evidence], [], []])
    assert result["terminal_action"] == "BLOCK_PATCH"


def test_trace_hash_is_deterministic_and_has_no_success_field():
    obligations = [Obligation("x", "identity", source=typed("pending"))]
    a = run_control_runtime(obligations, [[], []])
    b = run_control_runtime(obligations, [[], []])
    assert a["trace_sha256"] == b["trace_sha256"]
    assert "repair_success" not in a
    assert "pass" not in a
