from __future__ import annotations

from typing import Any

from evals.v3_chronological_replay import build_replay


def build_counterfactual_replay(rows: list[dict[str, Any]]) -> dict[str, Any]:
    from agents.experience import build_experiences, compatibility, task_signature

    replay = build_replay(rows)
    by_id = {str(row["id"]): row for row in rows}
    samples = []
    for window in replay["windows"]:
        positive = []
        negative = []
        excluded = []
        current = by_id[window["trajectory_id"]]
        context = task_signature(str(current.get("task") or ""), current.get("changed_paths") or [])
        for previous_id in window["eligible_past_trajectory_ids"]:
            experiences = build_experiences(by_id[previous_id])
            if not experiences:
                continue
            experience = experiences[0]
            item = {
                "trajectory_id": previous_id,
                "outcome": experience.outcome,
                "failure_type": experience.failure_type,
                "compatibility": compatibility(experience, context)[0],
            }
            if experience.outcome == "accepted":
                positive.append(item)
            elif experience.outcome in {"rejected", "failed"}:
                negative.append(item)
            else:
                excluded.append(item)
        samples.append(
            {
                "trajectory_id": window["trajectory_id"],
                "positive_past": positive,
                "negative_past": negative,
                "excluded_past": excluded,
                "counterfactual_ready": bool(positive and negative),
                "matched_positive": [item for item in positive if item["compatibility"] > 0],
                "matched_negative": [item for item in negative if item["compatibility"] > 0],
            }
        )
    for sample in samples:
        sample["matched_counterfactual_ready"] = bool(
            sample["matched_positive"] and sample["matched_negative"]
        )
    return {
        "protocol": "v3-counterfactual-replay-v1",
        "strict_past_only": True,
        "model_free": True,
        "samples": samples,
        "ready_pairs": sum(int(sample["counterfactual_ready"]) for sample in samples),
        "matched_ready_pairs": sum(
            int(sample["matched_counterfactual_ready"]) for sample in samples
        ),
        "claim_boundary": "Evidence availability only; no causal counterfactual effect is inferred.",
        "blockers": {
            "requires_execution_provenance": True,
            "requires_both_outcomes": True,
            "requires_compatible_positive_and_negative": True,
        },
    }
