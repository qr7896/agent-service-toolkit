from evals.e1c_strict_v5_official_metadata import deterministic_candidates


def test_official_candidate_selection_is_deterministic(monkeypatch) -> None:
    monkeypatch.setattr(
        "evals.e1c_strict_v5_official_metadata.locally_touched_ids",
        lambda: frozenset({"task-b"}),
    )
    inventory = [
        {"instance_id": "task-a", "task_yaml_path": "tasks/task-a/task.yaml"},
        {"instance_id": "task-b", "task_yaml_path": "tasks/task-b/task.yaml"},
        {"instance_id": "task-c", "task_yaml_path": "tasks/task-c/task.yaml"},
        {"instance_id": "task-d", "task_yaml_path": "tasks/task-d/task.yaml"},
    ]
    left = deterministic_candidates(inventory, limit=3)
    right = deterministic_candidates(list(reversed(inventory)), limit=3)
    assert left == right
    assert all(row["instance_id"] != "task-b" for row in left)
