from evals.v3_collection import collection_status, preflight


def test_collection_status_excludes_pre_marker_history():
    manifest = {
        "protocol": "v3-prospective-collection-v1",
        "collection_id": "cohort-1",
        "start_time": "2026-09-19T12:00:00+00:00",
        "trajectory_schema": "v3-trajectory-v1",
        "trajectory_path": "x.jsonl",
        "preflight_snapshot": {},
    }
    rows = [
        {"id": "old", "ended_at": "2026-09-18T12:00:00+00:00"},
        {"id": "new", "ended_at": "2026-09-19T13:00:00+00:00"},
    ]
    artifact = collection_status(manifest, rows)
    assert artifact["historical_rows_excluded"] == 1
    assert artifact["prospective_rows"] == 1
    assert artifact["readiness"]["details"][0]["id"] == "new"


def test_collection_status_reports_zero_without_new_rows():
    manifest = {
        "protocol": "v3-prospective-collection-v1",
        "collection_id": "cohort-1",
        "start_time": "2026-09-19T12:00:00+00:00",
        "trajectory_schema": "v3-trajectory-v1",
        "trajectory_path": "x.jsonl",
        "preflight_snapshot": {},
    }
    artifact = collection_status(manifest, [{"id": "old", "ended_at": "2026-09-18T12:00:00+00:00"}])
    assert artifact["prospective_rows"] == 0
    assert artifact["readiness"]["ready"] is False


def test_preflight_does_not_create_trajectory(tmp_path):
    trajectory = tmp_path / "coding_agent.jsonl"
    artifact = preflight(trajectory)
    assert isinstance(artifact["ready_to_collect"], bool)
    assert artifact["trajectory_parent_writable"] is True
    assert not trajectory.exists()
