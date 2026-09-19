import pytest

import agents.coding_agent as coding_agent
from agents.experience import build_experiences, compiler_config_hash


def test_compiler_uses_execution_commit_not_current_head(tmp_path):
    trajectory = {
        "id": "t1",
        "status": "succeeded",
        "ended_at": "2026-01-01T00:00:00+00:00",
        "task": "fix parser",
        "source_repo": "owner/repo",
        "source_commit_at_execution": "deadbeef",
        "changed_paths": [],
        "test_result": {"status": "passed"},
        "review": {"approved": True},
    }
    experience = build_experiences(trajectory, tmp_path)[0]
    assert experience.extra["schema_version"] == "v3-experience-v2"
    assert experience.extra["source_repo"] == "owner/repo"
    assert experience.extra["repo_commit"] == "deadbeef"
    assert experience.extra["event_time"] == trajectory["ended_at"]
    assert experience.extra["validation_strength"] == {
        "test_observed": True,
        "test_passed": True,
        "review_observed": True,
        "review_approved": True,
        "approval_observed": False,
        "write_approved": None,
    }
    assert experience.extra["lifecycle_state"] == "active"
    assert experience.extra["lifecycle_event_time"] == trajectory["ended_at"]
    assert experience.extra["compiler_config_hash"] == compiler_config_hash()


def test_compiler_does_not_invent_missing_commit(tmp_path):
    trajectory = {"id": "t2", "status": "failed", "task": "fix parser"}
    experience = build_experiences(trajectory, tmp_path)[0]
    assert experience.extra["repo_commit"] == ""
    assert experience.extra["applied"] is None
    assert experience.extra["validation_strength"]["test_observed"] is False
    assert experience.extra["lifecycle_state"] == "active"


@pytest.mark.asyncio
async def test_make_plan_captures_execution_commit(monkeypatch):
    async def fake_planner(state, config):
        return {"plan": {"steps": []}}

    monkeypatch.setattr(coding_agent, "planner", fake_planner)
    monkeypatch.setattr(coding_agent, "repo_commit", lambda root: "abc123")
    result = await coding_agent.make_plan(
        {"attempts": 0}, {"configurable": {"source_repo": "owner/repo"}}
    )
    assert result["source_repo"] == "owner/repo"
    assert result["source_commit_at_execution"] == "abc123"
    assert result["trajectory_started_at"]
