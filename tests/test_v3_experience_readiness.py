import json
import sqlite3

from evals.v3_experience_readiness import audit


def test_readiness_fails_closed_without_temporal_provenance(tmp_path):
    trajectories = tmp_path / "trajectories.jsonl"
    trajectories.write_text(
        json.dumps({"id": "t1", "status": "succeeded", "ended_at": "2026-01-01"})
        + "\n"
        + json.dumps({"id": "t2", "status": "completed_read_only"})
        + "\n",
        encoding="utf-8",
    )
    database = tmp_path / "experience.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE experiences (trajectory_id TEXT, created_at TEXT, outcome TEXT, "
            "failure_type TEXT, extra TEXT)"
        )
        connection.execute(
            "INSERT INTO experiences VALUES (?, ?, ?, ?, ?)",
            ("t1", "2026-01-01", "accepted", "", "{}"),
        )
    result = audit(trajectories, database)
    assert result["trajectory_inventory"]["compiler_eligible"] == 1
    assert not result["gates"]["schema_v2_ready"]
    assert not result["gates"]["temporal_provenance_ready"]
    assert not result["gates"]["continual_evaluation_ready"]
