from evals.e1b_protocol_invariants_v10_5 import INVARIANT_IDS, evaluate_invariants


def test_all_protocol_invariants_hold():
    report = evaluate_invariants()
    assert report["all_passed"] is True
    assert [row["invariant_id"] for row in report["invariants"]] == list(INVARIANT_IDS)
    assert all(row["passed"] for row in report["invariants"])


def test_invariant_report_is_deterministic():
    assert evaluate_invariants() == evaluate_invariants()


def test_invariant_report_has_no_efficacy_metric():
    report = evaluate_invariants()
    assert "repair_success" not in report
    assert "pass_rate" not in report
