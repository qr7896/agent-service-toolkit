import json

from evals import e1c_strict_v5_gate as gate


def test_strict_v5_gates_are_fail_closed_without_results(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(gate, "CANARY_RESULT", tmp_path / "canary.json")
    monkeypatch.setattr(gate, "DEV30_RESULT", tmp_path / "dev30.json")
    monkeypatch.setattr(gate, "FRESH30_IDENTITY", tmp_path / "fresh30.json")
    assert gate.canary_gate()["ready"] is False
    assert gate.c5_gate()["ready"] is False
    result = gate.fresh30_gate()
    assert result["ready"] is False
    assert result["materialization_allowed"] is False
    assert result["new_task_tree_touched"] is False


def test_strict_v5_fresh30_requires_canary_gain_and_dev30_30_of_30(tmp_path, monkeypatch) -> None:
    canary = tmp_path / "canary.json"
    dev30 = tmp_path / "dev30.json"
    monkeypatch.setattr(gate, "CANARY_RESULT", canary)
    monkeypatch.setattr(gate, "DEV30_RESULT", dev30)
    monkeypatch.setattr(gate, "FRESH30_IDENTITY", tmp_path / "fresh30.json")

    canary.write_text(json.dumps({
        "status": "completed",
        "treatment_only_resolved": ["task-a"],
        "baseline_only_resolved": [],
        "identity_anomalies": [],
    }), encoding="utf-8")
    dev30.write_text(json.dumps({
        "status": "completed",
        "identity_anomalies": [],
        "rows": [{"instance_id": f"t{i}", "resolved": True} for i in range(30)],
    }), encoding="utf-8")

    assert gate.canary_gate()["ready"] is True
    assert gate.c5_gate()["ready"] is True
    fresh = gate.fresh30_gate()
    assert fresh["ready"] is True
    assert fresh["materialization_allowed"] is True


def test_canary_baseline_only_gain_keeps_gate_closed(tmp_path, monkeypatch) -> None:
    canary = tmp_path / "canary.json"
    monkeypatch.setattr(gate, "CANARY_RESULT", canary)
    canary.write_text(json.dumps({
        "status": "completed",
        "treatment_only_resolved": ["task-a"],
        "baseline_only_resolved": ["task-b"],
        "identity_anomalies": [],
    }), encoding="utf-8")
    assert gate.canary_gate()["ready"] is False
