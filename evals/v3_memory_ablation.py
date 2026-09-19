from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evals.v3_chronological_replay import build_replay, load_jsonl

ARMS = ("no_memory", "always_on", "compatibility_only", "reliability_aware")


def summarize(samples: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {arm: 0 for arm in ARMS}
    pool = 0
    for sample in samples:
        pool += len(sample["eligible_pool"])
        for arm in ARMS:
            totals[arm] += len(sample["arms"][arm])
    return {
        "samples": len(samples),
        "eligible_pool_total": pool,
        "selected_total_by_arm": totals,
        "reliability_abstentions": pool - totals["reliability_aware"],
    }


def build_ablation(
    rows: list[dict[str, Any]],
    commit_distances: dict[tuple[str, str], int],
    threshold: float = 0.6,
) -> dict[str, Any]:
    from agents.experience import build_experiences, compatibility, task_signature
    from agents.experience_reliability import policy_decision

    replay = build_replay(rows)
    by_id = {str(row["id"]): row for row in rows}
    samples = []
    for window in replay["windows"]:
        current = by_id[window["trajectory_id"]]
        context = task_signature(str(current.get("task") or ""), current.get("changed_paths") or [])
        context["repo_commit"] = str(current.get("source_commit_at_execution") or "")
        arms: dict[str, list[str]] = {name: [] for name in ARMS}
        for previous_id in window["eligible_past_trajectory_ids"]:
            experiences = build_experiences(by_id[previous_id])
            if not experiences:
                continue
            experience = experiences[0]
            arms["always_on"].append(previous_id)
            compatibility_score, _ = compatibility(experience, context)
            if compatibility_score > 0:
                arms["compatibility_only"].append(previous_id)
            previous_commit = str(by_id[previous_id].get("source_commit_at_execution") or "")
            current_commit = str(current.get("source_commit_at_execution") or "")
            decision = policy_decision(
                experience,
                context,
                commit_distance=commit_distances.get((previous_commit, current_commit)),
                threshold=threshold,
            )
            if decision["adopt"]:
                arms["reliability_aware"].append(previous_id)
        samples.append(
            {
                "trajectory_id": window["trajectory_id"],
                "event_time": window["event_time"],
                "eligible_pool": window["eligible_past_trajectory_ids"],
                "arms": arms,
            }
        )
    artifact = {
        "protocol": "v3-memory-ablation-v1",
        "matched": True,
        "strict_past_only": True,
        "arms": list(ARMS),
        "samples": samples,
    }
    artifact["summary"] = summarize(samples)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trajectories", type=Path, required=True)
    parser.add_argument("--commit-distances", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.6)
    args = parser.parse_args()
    distances: dict[tuple[str, str], int] = {}
    if args.commit_distances:
        raw = json.loads(args.commit_distances.read_text(encoding="utf-8"))
        distances = {(str(item["from"]), str(item["to"])): int(item["distance"]) for item in raw}
    artifact = build_ablation(load_jsonl(args.trajectories), distances, args.threshold)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(artifact["summary"]))


if __name__ == "__main__":
    main()
