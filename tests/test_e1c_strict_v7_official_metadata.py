from evals.e1c_strict_v7_official_metadata import ranked_candidates


def test_v7_metadata_ranking_excludes_denylist_and_is_deterministic(monkeypatch) -> None:
    rows = [
        {"instance_id": "a", "path": "tasks/a/task.yaml"},
        {"instance_id": "b", "path": "tasks/b/task.yaml"},
        {"instance_id": "c", "path": "tasks/c/task.yaml"},
        {"instance_id": "d", "path": "tasks/d/task.yaml"},
    ]
    monkeypatch.setattr("evals.e1c_strict_v7_official_metadata.denylist", lambda: frozenset({"a"}))
    left = ranked_candidates(rows, limit=3)
    right = ranked_candidates(list(reversed(rows)), limit=3)
    assert [row["instance_id"] for row in left] == [row["instance_id"] for row in right]
    assert "a" not in [row["instance_id"] for row in left]
