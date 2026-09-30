import json

from evals import e1c_fresh30_gate_v2


def test_v2_gate_never_touches_fresh_tree_before_repro_canary(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(e1c_fresh30_gate_v2, "REPRO_CANARY_RUN", tmp_path / "canary")
    monkeypatch.setattr(e1c_fresh30_gate_v2, "FULL30_RUN", tmp_path / "c5")
    result = e1c_fresh30_gate_v2.gate()
    assert result["ready"] is False
    assert result["reason"] == "reproducer_canary_not_completed"
    assert result["new_task_tree_touched"] is False


def test_v2_gate_requires_canary_gain_before_c5(tmp_path, monkeypatch) -> None:
    canary = tmp_path / "canary"
    canary.mkdir()
    (canary / "result.json").write_text(json.dumps({"expand_c5": False}), encoding="utf-8")
    monkeypatch.setattr(e1c_fresh30_gate_v2, "REPRO_CANARY_RUN", canary)
    monkeypatch.setattr(e1c_fresh30_gate_v2, "FULL30_RUN", tmp_path / "c5")
    result = e1c_fresh30_gate_v2.gate()
    assert result["ready"] is False
    assert result["reason"] == "reproducer_canary_stop_rule_not_met"
    assert result["new_task_tree_touched"] is False


def test_v2_gate_requires_same_version_30_of_30(tmp_path, monkeypatch) -> None:
    canary = tmp_path / "canary"
    c5 = tmp_path / "c5"
    canary.mkdir()
    c5.mkdir()
    (canary / "result.json").write_text(json.dumps({"expand_c5": True}), encoding="utf-8")
    rows = [{"resolved": True} for _ in range(29)] + [{"resolved": False}]
    (c5 / "result.json").write_text(
        json.dumps({"status": "completed", "rows": rows}), encoding="utf-8"
    )
    monkeypatch.setattr(e1c_fresh30_gate_v2, "REPRO_CANARY_RUN", canary)
    monkeypatch.setattr(e1c_fresh30_gate_v2, "FULL30_RUN", c5)
    result = e1c_fresh30_gate_v2.gate()
    assert result["ready"] is False
    assert result["attempted"] == 30
    assert result["resolved"] == 29
    assert result["new_task_tree_touched"] is False
