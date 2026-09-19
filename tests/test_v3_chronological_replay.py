import pytest

from evals.v3_chronological_replay import build_policy_replay, build_replay


def row(identifier, ended_at, commit, repo="owner/repo"):
    return {
        "id": identifier,
        "ended_at": ended_at,
        "source_repo": repo,
        "source_commit_at_execution": commit,
    }


def test_replay_is_strictly_past_only_and_blocks_source_commit_aliases():
    artifact = build_replay(
        [
            row("later", "2026-01-03T00:00:00+00:00", "c3"),
            row("first", "2026-01-01T00:00:00+00:00", "c1"),
            row("alias", "2026-01-02T00:00:00+00:00", "c1"),
        ]
    )
    first, alias, later = artifact["windows"]
    assert first["eligible_past_trajectory_ids"] == []
    assert alias["eligible_past_trajectory_ids"] == []
    assert alias["blocked_source_commit_aliases"] == ["first"]
    assert later["eligible_past_trajectory_ids"] == ["first", "alias"]


def test_equal_time_uses_id_for_order_but_not_as_past_evidence():
    artifact = build_replay(
        [
            row("b", "2026-01-01T00:00:00+00:00", "c2"),
            row("a", "2026-01-01T00:00:00+00:00", "c1"),
        ]
    )
    assert [item["trajectory_id"] for item in artifact["windows"]] == ["a", "b"]
    assert artifact["windows"][1]["eligible_past_trajectory_ids"] == []


@pytest.mark.parametrize(
    "bad",
    [
        {"id": "x", "ended_at": "2026-01-01T00:00:00+00:00", "source_repo": "r"},
        {"id": "x", "ended_at": "2026-01-01T00:00:00+00:00", "source_commit_at_execution": "c"},
        {
            "id": "x",
            "ended_at": "2026-01-01T00:00:00",
            "source_repo": "r",
            "source_commit_at_execution": "c",
        },
    ],
)
def test_replay_fails_closed_on_missing_or_ambiguous_provenance(bad):
    with pytest.raises(ValueError):
        build_replay([bad])


def test_policy_replay_only_scores_strictly_past_experiences():
    first = {
        **row("first", "2026-01-01T00:00:00+00:00", "c1"),
        "status": "succeeded",
        "task": "fix fastapi route",
        "changed_paths": [],
        "test_result": {"status": "passed"},
        "review": {"approved": True},
    }
    later = {
        **row("later", "2026-01-02T00:00:00+00:00", "c2"),
        "status": "failed",
        "task": "fix fastapi endpoint",
        "changed_paths": [],
    }
    artifact = build_policy_replay([later, first], {("c1", "c2"): 1}, threshold=0.5)
    assert artifact["windows"][0]["policy_decisions"] == []
    decision = artifact["windows"][1]["policy_decisions"][0]
    assert decision["trajectory_id"] == "first"
    assert decision["adopt"] is True


def test_policy_replay_fails_closed_when_commit_distance_is_unavailable():
    first = {
        **row("first", "2026-01-01T00:00:00+00:00", "c1"),
        "status": "succeeded",
        "task": "fix fastapi route",
        "changed_paths": [],
    }
    later = {
        **row("later", "2026-01-02T00:00:00+00:00", "c2"),
        "status": "failed",
        "task": "fix fastapi endpoint",
        "changed_paths": [],
    }
    decision = build_policy_replay([first, later], {})["windows"][1]["policy_decisions"][0]
    assert decision["adopt"] is False
    assert decision["reason"] == "commit_distance_unknown"
