from evals import e1c_fresh30_gate_v4 as gate


def test_v4_fresh30_gate_is_closed_without_independent_canary(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(gate, "REPRO_V4_CANARY_RUN", tmp_path / "missing-canary")
    monkeypatch.setattr(gate, "FULL30_RUN", tmp_path / "missing-full30")
    result = gate.gate()
    assert result["ready"] is False
    assert result["reason"] == "reproducer_v4_independent_canary_not_completed"
    assert result["new_task_tree_touched"] is False
