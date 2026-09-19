from evals.v3_memory_ablation import ARMS, build_ablation


def test_four_arm_ablation_is_matched_and_past_only():
    rows = [
        {
            "id": "old",
            "ended_at": "2026-01-01T00:00:00+00:00",
            "status": "succeeded",
            "task": "fix fastapi route",
            "source_repo": "owner/repo",
            "source_commit_at_execution": "c1",
            "changed_paths": [],
            "test_result": {"status": "passed"},
            "review": {"approved": True},
        },
        {
            "id": "new",
            "ended_at": "2026-01-02T00:00:00+00:00",
            "status": "failed",
            "task": "fix fastapi endpoint",
            "source_repo": "owner/repo",
            "source_commit_at_execution": "c2",
            "changed_paths": [],
        },
    ]
    artifact = build_ablation(rows, {("c1", "c2"): 1}, threshold=0.5)
    assert tuple(artifact["arms"]) == ARMS
    assert artifact["samples"][0]["eligible_pool"] == []
    second = artifact["samples"][1]
    assert second["arms"]["no_memory"] == []
    assert second["arms"]["always_on"] == ["old"]
    assert second["arms"]["compatibility_only"] == ["old"]
    assert second["arms"]["reliability_aware"] == ["old"]


def test_reliability_arm_abstains_when_distance_is_missing():
    rows = [
        {
            "id": "a",
            "ended_at": "2026-01-01T00:00:00+00:00",
            "status": "succeeded",
            "task": "fix fastapi route",
            "source_repo": "r",
            "source_commit_at_execution": "c1",
            "changed_paths": [],
        },
        {
            "id": "b",
            "ended_at": "2026-01-02T00:00:00+00:00",
            "status": "failed",
            "task": "fix fastapi endpoint",
            "source_repo": "r",
            "source_commit_at_execution": "c2",
            "changed_paths": [],
        },
    ]
    second = build_ablation(rows, {})["samples"][1]
    assert second["arms"]["always_on"] == ["a"]
    assert second["arms"]["reliability_aware"] == []


def test_ablation_summary_is_audit_only():
    rows = [
        {
            "id": "a",
            "ended_at": "2026-01-01T00:00:00+00:00",
            "status": "succeeded",
            "task": "fix route",
            "source_repo": "r",
            "source_commit_at_execution": "c1",
            "changed_paths": [],
        },
        {
            "id": "b",
            "ended_at": "2026-01-02T00:00:00+00:00",
            "status": "failed",
            "task": "fix route",
            "source_repo": "r",
            "source_commit_at_execution": "c2",
            "changed_paths": [],
        },
    ]
    summary = build_ablation(rows, {})["summary"]
    assert summary["eligible_pool_total"] == 1
    assert summary["selected_total_by_arm"]["no_memory"] == 0
    assert summary["reliability_abstentions"] == 1
