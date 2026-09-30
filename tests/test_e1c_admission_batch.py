"""The replacement batch must preserve the frozen original-first order."""

import json

import pytest

from evals import e1c_admission_batch as batch


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_replacement_batch_requires_original_results_and_verified_inventories(tmp_path, monkeypatch):
    monkeypatch.setattr(batch, "OUT", tmp_path)
    original = [{"instance_id": f"original-{i}"} for i in range(30)]
    replacement = [{"instance_id": "replacement"}]
    _write(tmp_path / "candidate_manifest.json", {
        "status": "selected_not_admitted", "count": 30, "tasks": original,
    })
    _write(tmp_path / "cohort_preparation_status.json", {
        "selection_mode": "network_bounded", "replacement_pool_partial": False,
        "frozen_candidate_count": 30, "replacement_pool": replacement,
    })
    _write(tmp_path / "replacement_task_inventory.json", {
        "tasks": [{"instance_id": "replacement", "materialization_status": "complete"}],
    })
    _write(tmp_path / "replacement_source_inventory.json", {
        "tasks": [{"instance_id": "replacement", "match": True}],
    })
    assert batch.load_rows() == original
    with pytest.raises(ValueError, match="original 30"):
        batch.load_rows(True)
    for row in original:
        for phase in ("base", "gold"):
            _write(tmp_path / "admission_v2" / row["instance_id"] / f"{phase}.json", {})
    assert batch.load_rows(True) == replacement
    _write(tmp_path / "replacement_source_inventory.json", {
        "tasks": [{"instance_id": "replacement", "match": False}],
    })
    with pytest.raises(ValueError, match="not verified"):
        batch.load_rows(True)
