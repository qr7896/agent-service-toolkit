import json

from scripts.export_v3_experiences import export


def test_export_is_non_destructive_and_preserves_missing_provenance(tmp_path):
    trajectories = tmp_path / "trajectories.jsonl"
    output = tmp_path / "export.json"
    source = {
        "id": "old-1",
        "status": "failed",
        "ended_at": "2026-01-01T00:00:00+00:00",
        "task": "fix parser",
        "test_result": {"status": "failed"},
    }
    trajectories.write_text(json.dumps(source) + "\n", encoding="utf-8")
    before = trajectories.read_bytes()

    artifact = export(trajectories, output, tmp_path)

    assert trajectories.read_bytes() == before
    assert artifact["rows_compiled"] == 1
    experience = artifact["experiences"][0]
    assert experience["extra"]["schema_version"] == "v3-experience-v2"
    assert experience["extra"]["repo_commit"] == ""
    assert experience["extra"]["lifecycle_state"] == "active"
    assert experience["extra"]["compiler_config_hash"]
    assert json.loads(output.read_text(encoding="utf-8"))["protocol"] == "v3-experience-export-v1"
