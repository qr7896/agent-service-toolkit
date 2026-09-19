from agents.experience import build_experiences
from agents.experience_reliability import (
    adjudicate_conflict,
    adoption_decision,
    decay_factor,
    experiences_conflict,
    lifecycle_transition,
    policy_decision,
    reliability_score,
)


def test_reliability_rewards_independent_validation():
    extra = {
        "lifecycle_state": "active",
        "validation_strength": {"test_passed": True, "review_approved": True},
    }
    assert reliability_score(extra) == 0.85
    assert adoption_decision(extra)["adopt"] is True


def test_reliability_abstains_for_invalidated_or_harmful_memory():
    invalidated = {
        "lifecycle_state": "invalidated",
        "validation_strength": {"test_passed": True, "review_approved": True},
    }
    harmful = {
        "lifecycle_state": "active",
        "validation_strength": {"test_passed": False, "review_approved": False},
        "used_count": 3,
        "helped_count": 0,
        "harmful_count": 3,
    }
    assert reliability_score(invalidated) == 0.0
    assert adoption_decision(invalidated)["adopt"] is False
    assert reliability_score(harmful) == 0.05
    assert reliability_score(harmful, include_usage=True) == 0.0
    assert adoption_decision(harmful)["adopt"] is False


def test_policy_combines_reliability_compatibility_and_commit_distance():
    trajectory = {
        "id": "old",
        "status": "succeeded",
        "ended_at": "2026-01-01T00:00:00+00:00",
        "task": "fix fastapi route",
        "source_repo": "owner/repo",
        "source_commit_at_execution": "c1",
        "changed_paths": [],
        "test_result": {"status": "passed"},
        "review": {"approved": True},
    }
    experience = build_experiences(trajectory)[0]
    experience.extra["task_signature"] = {
        "domain": "fastapi",
        "issue_type": "bug_fix",
        "language": "python",
    }
    context = {
        "domain": "fastapi",
        "issue_type": "bug_fix",
        "language": "python",
        "repo_commit": "c2",
    }
    near = policy_decision(experience, context, commit_distance=1, threshold=0.5)
    unknown = policy_decision(experience, context, commit_distance=None, threshold=0.5)
    assert near["adopt"] is True
    assert near["commit_factor"] > 0.9
    assert unknown["adopt"] is False
    assert unknown["reason"] == "commit_distance_unknown"


def test_conflict_detection_and_reversible_isolation():
    base = {
        "ended_at": "2026-01-01T00:00:00+00:00",
        "task": "fix fastapi route",
        "source_repo": "owner/repo",
        "source_commit_at_execution": "c1",
        "changed_paths": [],
    }
    accepted = build_experiences({**base, "id": "a", "status": "succeeded"})[0]
    rejected = build_experiences({**base, "id": "b", "status": "failed"})[0]
    assert experiences_conflict(accepted, rejected) is True
    isolated = lifecycle_transition(
        accepted.extra, conflict=True, reason="opposite outcome", event_time="t2"
    )
    assert isolated["lifecycle_state"] == "isolated"
    revived = lifecycle_transition(isolated, conflict=False, event_time="t3")
    assert revived["lifecycle_state"] == "active"


def test_decay_and_conflict_adjudication_prefer_stronger_recent_evidence():
    base = {
        "ended_at": "2026-01-01T00:00:00+00:00",
        "task": "fix fastapi route",
        "source_repo": "owner/repo",
        "source_commit_at_execution": "c1",
        "changed_paths": [],
    }
    older = build_experiences({**base, "id": "old", "status": "failed"})[0]
    newer = build_experiences(
        {
            **base,
            "id": "new",
            "status": "succeeded",
            "test_result": {"status": "passed"},
            "review": {"approved": True},
        }
    )[0]
    result = adjudicate_conflict(older, newer, left_age_events=20, right_age_events=1)
    assert decay_factor(age_events=20) == 0.5
    assert result["action"] == "isolate_loser"
    assert result["winner"] == "new"


def test_replay_default_ignores_untimestamped_lifetime_usage():
    base = {
        "lifecycle_state": "active",
        "validation_strength": {"test_passed": True, "review_approved": True},
    }
    future_feedback = {**base, "used_count": 100, "helped_count": 0, "harmful_count": 100}
    assert reliability_score(base) == reliability_score(future_feedback)
    assert reliability_score(future_feedback, include_usage=True) < reliability_score(base)
