from evals.e1c_blind_resume import _summary


def test_resume_summary_requires_net_new_without_loss() -> None:
    rows = [
        {"instance_id": "a", "arm": "baseline", "resolved": True},
        {"instance_id": "a", "arm": "structured", "resolved": True},
        {"instance_id": "b", "arm": "baseline", "resolved": False},
        {"instance_id": "b", "arm": "structured", "resolved": True},
    ]
    result = _summary(rows)
    assert result["baseline_resolved"] == 1
    assert result["structured_resolved"] == 2
    assert result["net_new_resolved"] == 1
    assert result["lost_resolved"] == 0
    assert result["expand_b5"] is True


def test_resume_summary_stops_when_structured_loses_baseline() -> None:
    rows = [
        {"instance_id": "a", "arm": "baseline", "resolved": True},
        {"instance_id": "a", "arm": "structured", "resolved": False},
        {"instance_id": "b", "arm": "baseline", "resolved": False},
        {"instance_id": "b", "arm": "structured", "resolved": True},
    ]
    result = _summary(rows)
    assert result["net_new_resolved"] == 1
    assert result["lost_resolved"] == 1
    assert result["expand_b5"] is False
