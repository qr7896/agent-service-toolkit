import json

from evals import e1c_fresh30_gate


def test_fresh30_gate_does_not_touch_new_task_tree_before_c4(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(e1c_fresh30_gate, "POSTB4_RUN", tmp_path / "c4")
    monkeypatch.setattr(e1c_fresh30_gate, "FULL30_RUN", tmp_path / "c5")
    result = e1c_fresh30_gate.gate()
    assert result["ready"] is False
    assert result["reason"] == "C4_not_completed"
    assert result["new_task_tree_touched"] is False


def test_fresh30_gate_requires_exact_same_version_30_of_30(tmp_path, monkeypatch) -> None:
    c4 = tmp_path / "c4"
    c5 = tmp_path / "c5"
    c4.mkdir()
    c5.mkdir()
    (c4 / "result.json").write_text(json.dumps({"expand_c5": True}), encoding="utf-8")
    rows = [{"resolved": True} for _ in range(29)] + [{"resolved": False}]
    (c5 / "result.json").write_text(
        json.dumps({"status": "completed", "rows": rows}), encoding="utf-8"
    )
    monkeypatch.setattr(e1c_fresh30_gate, "POSTB4_RUN", c4)
    monkeypatch.setattr(e1c_fresh30_gate, "FULL30_RUN", c5)
    result = e1c_fresh30_gate.gate()
    assert result["ready"] is False
    assert result["attempted"] == 30
    assert result["resolved"] == 29
    assert result["new_task_tree_touched"] is False
