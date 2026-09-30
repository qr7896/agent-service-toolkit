import json

import evals.e1c_strict_v5_stage_a_gate as gate


def _write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def test_stage_a_ready_does_not_open_live_gates(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "workspace.json"
    legacy = tmp_path / "legacy.json"
    contamination = tmp_path / "contamination.json"
    _write(
        workspace,
        {
            "identity_sha256": "a" * 64,
            "identity_file_count": 10,
            "workspace_identity_required": True,
            "head_is_sufficient_identity": False,
        },
    )
    _write(
        legacy,
        {
            "seal_sha256": "b" * 64,
            "sealed_file_count": 5,
            "legacy_results_authoritative_for_v5": False,
        },
    )
    _write(
        contamination,
        {
            "unique_identity_count": 20,
            "provider_calls": 0,
            "new_task_tree_touched": False,
        },
    )
    monkeypatch.setattr(gate, "WORKSPACE_SNAPSHOT", workspace)
    monkeypatch.setattr(gate, "LEGACY_SEAL", legacy)
    monkeypatch.setattr(gate, "CONTAMINATION", contamination)
    monkeypatch.setattr(gate, "verify_workspace", lambda path: {"match": True})
    monkeypatch.setattr(gate, "verify_legacy", lambda path: {"match": True})
    result = gate.build(tmp_path / "out.json")
    assert result["stage_a_ready"] is True
    assert result["live_allowed"] is False
    assert result["canary_allowed"] is False
    assert result["c5_allowed"] is False
    assert result["fresh30_allowed"] is False


def test_stage_a_fails_on_workspace_drift(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "workspace.json"
    legacy = tmp_path / "legacy.json"
    contamination = tmp_path / "contamination.json"
    _write(
        workspace,
        {
            "identity_sha256": "a" * 64,
            "workspace_identity_required": True,
            "head_is_sufficient_identity": False,
        },
    )
    _write(
        legacy,
        {
            "legacy_results_authoritative_for_v5": False,
        },
    )
    _write(
        contamination,
        {"provider_calls": 0, "new_task_tree_touched": False},
    )
    monkeypatch.setattr(gate, "WORKSPACE_SNAPSHOT", workspace)
    monkeypatch.setattr(gate, "LEGACY_SEAL", legacy)
    monkeypatch.setattr(gate, "CONTAMINATION", contamination)
    monkeypatch.setattr(gate, "verify_workspace", lambda path: {"match": False})
    monkeypatch.setattr(gate, "verify_legacy", lambda path: {"match": True})
    result = gate.build(tmp_path / "out.json")
    assert result["stage_a_ready"] is False
    assert result["checks"]["workspace_snapshot_current"] is False


def test_stage_a_fails_on_legacy_drift(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "workspace.json"
    legacy = tmp_path / "legacy.json"
    contamination = tmp_path / "contamination.json"
    _write(
        workspace,
        {
            "identity_sha256": "a" * 64,
            "workspace_identity_required": True,
            "head_is_sufficient_identity": False,
        },
    )
    _write(legacy, {"legacy_results_authoritative_for_v5": False})
    _write(
        contamination,
        {"provider_calls": 0, "new_task_tree_touched": False},
    )
    monkeypatch.setattr(gate, "WORKSPACE_SNAPSHOT", workspace)
    monkeypatch.setattr(gate, "LEGACY_SEAL", legacy)
    monkeypatch.setattr(gate, "CONTAMINATION", contamination)
    monkeypatch.setattr(gate, "verify_workspace", lambda path: {"match": True})
    monkeypatch.setattr(gate, "verify_legacy", lambda path: {"match": False})
    result = gate.build(tmp_path / "out.json")
    assert result["stage_a_ready"] is False
    assert result["checks"]["legacy_artifacts_unchanged"] is False
