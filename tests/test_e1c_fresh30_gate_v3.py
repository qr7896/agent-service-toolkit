import json

from evals import e1c_fresh30_gate_v3


def test_v3_gate_stays_closed_before_final_canary(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(e1c_fresh30_gate_v3, "REPRO_V3_CANARY_RUN", tmp_path / "canary")
    monkeypatch.setattr(e1c_fresh30_gate_v3, "FULL30_RUN", tmp_path / "c5")
    result = e1c_fresh30_gate_v3.gate()
    assert result["ready"] is False
    assert result["reason"] == "reproducer_v3_canary_not_completed"
    assert result["new_task_tree_touched"] is False


def test_v3_gate_requires_treatment_only_canary_gain(tmp_path, monkeypatch) -> None:
    canary = tmp_path / "canary"
    canary.mkdir()
    (canary / "result.json").write_text(json.dumps({"expand_c5": False}), encoding="utf-8")
    monkeypatch.setattr(e1c_fresh30_gate_v3, "REPRO_V3_CANARY_RUN", canary)
    monkeypatch.setattr(e1c_fresh30_gate_v3, "FULL30_RUN", tmp_path / "c5")
    result = e1c_fresh30_gate_v3.gate()
    assert result["ready"] is False
    assert result["reason"] == "reproducer_v3_canary_stop_rule_not_met"
    assert result["new_task_tree_touched"] is False


def test_v3_gate_requires_exact_30_of_30(tmp_path, monkeypatch) -> None:
    canary = tmp_path / "canary"
    c5 = tmp_path / "c5"
    canary.mkdir()
    c5.mkdir()
    (canary / "result.json").write_text(json.dumps({"expand_c5": True}), encoding="utf-8")
    rows = [{"resolved": True} for _ in range(29)] + [{"resolved": False}]
    (c5 / "result.json").write_text(json.dumps({"status": "completed", "rows": rows}), encoding="utf-8")
    monkeypatch.setattr(e1c_fresh30_gate_v3, "REPRO_V3_CANARY_RUN", canary)
    monkeypatch.setattr(e1c_fresh30_gate_v3, "FULL30_RUN", c5)
    result = e1c_fresh30_gate_v3.gate()
    assert result["ready"] is False
    assert result["attempted"] == 30
    assert result["resolved"] == 29
    assert result["new_task_tree_touched"] is False
