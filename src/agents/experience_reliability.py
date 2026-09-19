from __future__ import annotations

from typing import Any

from agents.experience import Experience, compatibility


def reliability_score(extra: dict[str, Any], *, include_usage: bool = False) -> float:
    if str(extra.get("lifecycle_state") or "active") != "active":
        return 0.0
    validation = extra.get("validation_strength") or {}
    score = 0.5
    if validation.get("test_passed") is True:
        score += 0.2
    elif validation.get("test_passed") is False:
        score -= 0.25
    if validation.get("review_approved") is True:
        score += 0.15
    elif validation.get("review_approved") is False:
        score -= 0.2
    if include_usage:
        used = int(extra.get("used_count") or 0)
        helped = int(extra.get("helped_count") or 0)
        harmful = int(extra.get("harmful_count") or 0)
        if used:
            score += 0.2 * ((helped - harmful) / used)
    if extra.get("survival") == "reverted" or extra.get("likely_effective") is False:
        score -= 0.3
    return round(max(0.0, min(1.0, score)), 3)


def adoption_decision(extra: dict[str, Any], threshold: float = 0.6) -> dict[str, Any]:
    score = reliability_score(extra)
    lifecycle = str(extra.get("lifecycle_state") or "active")
    if lifecycle != "active":
        reason = f"lifecycle={lifecycle}"
    elif score < threshold:
        reason = f"reliability={score:.3f}<threshold={threshold:.3f}"
    else:
        reason = "reliability_threshold_met"
    return {"adopt": lifecycle == "active" and score >= threshold, "score": score, "reason": reason}


def policy_decision(
    experience: Experience,
    context: dict[str, str],
    *,
    commit_distance: int | None,
    threshold: float = 0.6,
) -> dict[str, Any]:
    if commit_distance is None or commit_distance < 0:
        return {
            "adopt": False,
            "score": 0.0,
            "reliability": reliability_score(experience.extra or {}),
            "compatibility": 0.0,
            "commit_factor": 0.0,
            "reason": "commit_distance_unknown",
        }
    compatibility_score, reasons = compatibility(experience, context)
    reliability = reliability_score(experience.extra or {})
    commit_factor = round(1.0 / (1.0 + commit_distance / 10.0), 3)
    score = round(reliability * compatibility_score * commit_factor, 3)
    return {
        "adopt": score >= threshold,
        "score": score,
        "reliability": reliability,
        "compatibility": compatibility_score,
        "commit_factor": commit_factor,
        "reason": "policy_threshold_met"
        if score >= threshold
        else "; ".join(reasons) or "policy_below_threshold",
    }


def lifecycle_transition(
    extra: dict[str, Any],
    *,
    conflict: bool = False,
    reason: str = "",
    event_time: str = "",
) -> dict[str, Any]:
    updated = dict(extra)
    current = str(updated.get("lifecycle_state") or "active")
    if conflict:
        updated["lifecycle_state"] = "isolated"
        updated["lifecycle_reason"] = reason or "conflicting_experience"
        updated["lifecycle_event_time"] = event_time
    elif current == "isolated":
        updated["lifecycle_state"] = "active"
        updated["lifecycle_reason"] = "conflict_cleared"
        updated["lifecycle_event_time"] = event_time
    return updated


def experiences_conflict(left: Experience, right: Experience) -> bool:
    left_signature = (left.extra or {}).get("task_signature") or {}
    right_signature = (right.extra or {}).get("task_signature") or {}
    return (
        left.outcome != right.outcome and left_signature == right_signature and bool(left_signature)
    )


def decay_factor(*, age_events: int, half_life_events: int = 20) -> float:
    if age_events < 0 or half_life_events <= 0:
        return 0.0
    return round(0.5 ** (age_events / half_life_events), 3)


def adjudicate_conflict(
    left: Experience,
    right: Experience,
    *,
    left_age_events: int,
    right_age_events: int,
) -> dict[str, Any]:
    if not experiences_conflict(left, right):
        return {"conflict": False, "winner": None, "action": "keep_both"}
    left_score = reliability_score(left.extra or {}) * decay_factor(age_events=left_age_events)
    right_score = reliability_score(right.extra or {}) * decay_factor(age_events=right_age_events)
    if round(left_score, 6) == round(right_score, 6):
        return {
            "conflict": True,
            "winner": None,
            "action": "isolate_both",
            "scores": [left_score, right_score],
        }
    winner = left.trajectory_id if left_score > right_score else right.trajectory_id
    loser = right.trajectory_id if winner == left.trajectory_id else left.trajectory_id
    return {
        "conflict": True,
        "winner": winner,
        "loser": loser,
        "action": "isolate_loser",
        "scores": [round(left_score, 3), round(right_score, 3)],
    }
