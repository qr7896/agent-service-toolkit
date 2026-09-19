from agents.trajectory import build_trajectory


def test_build_trajectory_preserves_execution_commit():
    state = {
        "messages": [],
        "trajectory_started_at": "2026-09-19T00:00:00+00:00",
        "source_repo": "owner/repo",
        "source_commit_at_execution": "abc123",
    }
    record = build_trajectory(state, {"configurable": {}})
    assert record["source_repo"] == "owner/repo"
    assert record["source_commit_at_execution"] == "abc123"
    assert record["adopted_experience_ids"] is None
    assert record["adoption_observed"] is False


def test_build_trajectory_separates_retrieved_and_adopted_experiences():
    state = {
        "messages": [],
        "source_repo": "owner/repo",
        "source_commit_at_execution": "abc123",
        "experience_hits": [
            {"trajectory_id": "retrieved-only", "adopted": False},
            {"trajectory_id": "adopted", "adopted": True},
        ],
    }
    record = build_trajectory(state, {"configurable": {}})
    assert record["experience_ids"] == ["adopted", "retrieved-only"]
    assert record["adopted_experience_ids"] == ["adopted"]


def test_build_trajectory_observes_explicit_non_adoption():
    state = {
        "messages": [],
        "source_repo": "owner/repo",
        "source_commit_at_execution": "abc123",
        "experience_hits": [{"trajectory_id": "retrieved-only", "adopted": False}],
    }
    record = build_trajectory(state, {"configurable": {}})
    assert record["experience_ids"] == ["retrieved-only"]
    assert record["adoption_observed"] is True
    assert record["adopted_experience_ids"] == []
