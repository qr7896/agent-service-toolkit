import json

from evals.v2_manifest import build_dataset_manifest, verify_dataset_manifest


def test_manifest_hashes_dataset_and_sources(tmp_path):
    dataset = tmp_path / "d.jsonl"
    source = tmp_path / "s.json"
    row = {
        "schema_version": "v2-decision-v1", "reward_config_sha256": "x",
        "task_id": "t", "step": 0,
        "state": {"split": "train", "cluster": "c", "source_commit": "k"},
        "candidates": [{"action": "stop", "propensity": 1.0, "policy_score": 0.0}],
        "chosen_action": "stop",
    }
    dataset.write_text(json.dumps(row) + "\n", encoding="utf-8")
    source.write_text("source", encoding="utf-8")
    manifest = build_dataset_manifest(dataset, [source], min_records=1)
    assert manifest["validation"]["ready_for_replay"] is True
    assert verify_dataset_manifest(manifest) == []


def test_manifest_detects_source_mutation(tmp_path):
    dataset = tmp_path / "d.jsonl"
    source = tmp_path / "s.json"
    row = {
        "schema_version": "v2-decision-v1", "reward_config_sha256": "x",
        "task_id": "t", "step": 0, "state": {},
        "candidates": [{"action": "stop", "propensity": 1.0, "policy_score": 0.0}],
        "chosen_action": "stop",
    }
    dataset.write_text(json.dumps(row) + "\n", encoding="utf-8")
    source.write_text("before", encoding="utf-8")
    manifest = build_dataset_manifest(dataset, [source], min_records=2)
    source.write_text("after", encoding="utf-8")
    assert verify_dataset_manifest(manifest)[0]["path"] == source.as_posix()
