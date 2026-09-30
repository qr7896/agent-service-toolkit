from evals.e1c_blind_repro_v4_runner import _summary


def test_v4_summary_requires_treatment_only_gain_without_anomaly() -> None:
    rows = [
        {"instance_id": "a", "arm": "baseline", "resolved": False, "status": "abstain", "usages": []},
        {"instance_id": "a", "arm": "treatment", "resolved": True, "status": "graded", "grade_valid_log": True, "usages": []},
    ]
    result = _summary(rows)
    assert result["treatment_only_resolved"] == ["a"]
    assert result["baseline_only_resolved"] == []
    assert result["identity_anomalies"] == []
    assert result["expand_c5"] is True


def test_v4_summary_keeps_c5_closed_on_invalid_grade_log() -> None:
    rows = [
        {"instance_id": "a", "arm": "baseline", "resolved": False, "status": "abstain", "usages": []},
        {"instance_id": "a", "arm": "treatment", "resolved": True, "status": "graded", "grade_valid_log": False, "usages": []},
    ]
    result = _summary(rows)
    assert result["identity_anomalies"]
    assert result["expand_c5"] is False
