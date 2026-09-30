from evals.e1c_strict_v6_official_metadata import ranked_candidates


def test_v6_candidate_ranking_excludes_touched_and_is_deterministic(monkeypatch) -> None:
    monkeypatch.setattr(
        "evals.e1c_strict_v6_official_metadata.denylist",
        lambda: frozenset({"b"}),
    )
    rows = [
        {"instance_id": "a", "path": "tasks/a/task.yaml"},
        {"instance_id": "b", "path": "tasks/b/task.yaml"},
        {"instance_id": "c", "path": "tasks/c/task.yaml"},
        {"instance_id": "d", "path": "tasks/d/task.yaml"},
    ]
    left = ranked_candidates(rows, limit=3)
    right = ranked_candidates(list(reversed(rows)), limit=3)
    assert left == right
    assert {row["instance_id"] for row in left} == {"a", "c", "d"}
