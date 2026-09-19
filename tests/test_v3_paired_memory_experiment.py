import json
from pathlib import Path

from evals.v3_paired_memory_experiment import build_pair_manifest, load_distances, preflight


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
