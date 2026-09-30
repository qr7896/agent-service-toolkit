import json

import pytest

from evals import e1c_dev_v22_recovery as recovery


def test_recovery_preflight_is_single_task_with_separate_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(recovery, "RUN_DIR", tmp_path / "unused")
    source = tmp_path / "source"
    source.mkdir()
    monkeypatch.setattr(recovery, "_source", lambda row: source)
    base = json.loads(
        (recovery.OUT / "admission_v2" / recovery.TASK_ID / "base.json").read_text(
            encoding="utf-8"
        )
    )
    monkeypatch.setattr(
        recovery.subprocess,
        "check_output",
        lambda *args, **kwargs: base["image_digest"],
    )
    gate, row, payload = recovery.preflight()
    assert gate["task_id"] == row["instance_id"] == recovery.TASK_ID
    assert gate["parent_run_id"] != gate["run_id"]
    assert gate["reserve"] <= gate["remaining_task_ceiling"]
    assert payload["excerpts"]


def test_recovery_preflight_rejects_image_digest_mismatch(tmp_path, monkeypatch):
    monkeypatch.setattr(recovery, "RUN_DIR", tmp_path / "unused")
    source = tmp_path / "source"
    source.mkdir()
    monkeypatch.setattr(recovery, "_source", lambda row: source)
    monkeypatch.setattr(
        recovery.subprocess,
        "check_output",
        lambda *args, **kwargs: "swebench/example@sha256:" + "0" * 64,
    )
    with pytest.raises(ValueError, match="official image admission changed"):
        recovery.preflight()
