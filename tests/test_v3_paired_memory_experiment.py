import asyncio
import json
from pathlib import Path

import pytest

from evals.v3_paired_memory_experiment import build_pair_manifest, load_distances, preflight
from evals.v3_paired_memory_live import _validate_pair, run


def test_load_distances(tmp_path: Path):
    p=tmp_path / "d.json"
    p.write_text(json.dumps([{"from":"a","to":"b","distance":3}]),encoding="utf-8")
    assert load_distances(p)=={("a","b"):3}


def test_preflight_is_offline_and_keeps_default_threshold(tmp_path: Path):
    trajectories=tmp_path / "rows.jsonl"
    trajectories.write_text("",encoding="utf-8")
    distances=tmp_path / "d.json"
    distances.write_text("[]",encoding="utf-8")
    result=preflight(trajectories,distances)
    assert result["provider_calls"]==0
    assert result["default_threshold"]==0.6
    assert result["ready_for_default_threshold_pair"] is False
    assert "no memory efficacy claim" in result["claim_boundary"]


def test_pair_manifest_empty_rows_is_not_ready(tmp_path: Path):
    trajectories=tmp_path / "rows.jsonl"
    trajectories.write_text("",encoding="utf-8")
    distances=tmp_path / "d.json"
    distances.write_text("[]",encoding="utf-8")
    result=build_pair_manifest(trajectories,distances)
    assert result["provider_calls"]==0
    assert result["threshold"]==0.375
    assert result["pairs"]==[]
    assert result["ready"] is False


def _valid_pair():
    return {
        "eligible_experience_ids": ["past-1"],
        "arms": [
            {"name": "memory_off", "memory_enabled": False},
            {"name": "memory_on", "memory_enabled": True},
        ],
        "invariants": {
            "same_task": True,
            "same_source_commit": True,
            "same_model": True,
            "same_token_ceiling": True,
            "same_grader": True,
            "strict_past_only": True,
        },
    }


def test_live_pair_validation_is_fail_closed():
    _validate_pair(_valid_pair())
    invalid = _valid_pair()
    invalid["invariants"]["strict_past_only"] = False
    with pytest.raises(ValueError, match="invariants"):
        _validate_pair(invalid)


def test_live_pair_does_not_overwrite_finalized_run(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "comparison.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError, match="already finalized"):
        asyncio.run(run(tmp_path / "missing-manifest.json", run_dir=run_dir))
