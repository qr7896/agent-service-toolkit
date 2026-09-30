from evals import e1c_fresh30_plan_v4 as plan


def test_fresh30_v4_plan_never_materializes_when_gate_closed(monkeypatch) -> None:
    monkeypatch.setattr(plan, "gate", lambda: {"ready": False, "reason": "independent_canary_missing", "new_task_tree_touched": False})
    result = plan.plan()
    assert result["provider_calls"] == 0
    assert result["materialization_allowed_now"] is False
    assert result["new_task_tree_touched"] is False
    assert result["target_task_count"] == 30
