from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _event_key(row: dict[str, Any]) -> tuple[datetime, str]:
    event_time = str(row.get("ended_at") or "")
    trajectory_id = str(row.get("id") or "")
    if not event_time or not trajectory_id:
        raise ValueError("trajectory requires ended_at and immutable id")
    try:
        parsed = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid ended_at for trajectory {trajectory_id}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"ended_at must be timezone-aware for trajectory {trajectory_id}")
    return parsed, trajectory_id


def _source_key(row: dict[str, Any]) -> tuple[str, str]:
    repo = str(row.get("source_repo") or "")
    commit = str(row.get("source_commit_at_execution") or "")
    if not repo or not commit:
        raise ValueError(f"trajectory {row.get('id') or '<missing>'} lacks source provenance")
    return repo, commit


def build_replay(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=_event_key)
    windows: list[dict[str, Any]] = []
    seen: list[dict[str, Any]] = []
    for row in ordered:
        event_time, trajectory_id = _event_key(row)
        source_key = _source_key(row)
        eligible = []
        blocked_aliases = []
        for previous in seen:
            previous_time, previous_id = _event_key(previous)
            if previous_time >= event_time:
                continue
            if _source_key(previous) == source_key:
                blocked_aliases.append(previous_id)
                continue
            eligible.append(previous_id)
        windows.append(
            {
                "trajectory_id": trajectory_id,
                "event_time": row["ended_at"],
                "source_repo": source_key[0],
                "source_commit_at_execution": source_key[1],
                "eligible_past_trajectory_ids": eligible,
                "blocked_source_commit_aliases": blocked_aliases,
            }
        )
        seen.append(row)
    return {
        "protocol": "v3-chronological-replay-v1",
        "ordering": "event_time_then_immutable_trajectory_id",
        "strict_past_only": True,
        "source_commit_alias_blocking": True,
        "rows": len(ordered),
        "windows": windows,
    }


def build_policy_replay(
    rows: list[dict[str, Any]],
    commit_distances: dict[tuple[str, str], int],
    threshold: float = 0.6,
) -> dict[str, Any]:
    from agents.experience import build_experiences, task_signature
    from agents.experience_reliability import policy_decision

    replay = build_replay(rows)
    by_id = {str(row["id"]): row for row in rows}
    policy_windows = []
    for window in replay["windows"]:
        current = by_id[window["trajectory_id"]]
        context = task_signature(str(current.get("task") or ""), current.get("changed_paths") or [])
        context["repo_commit"] = str(current.get("source_commit_at_execution") or "")
        decisions = []
        for previous_id in window["eligible_past_trajectory_ids"]:
            previous = by_id[previous_id]
            experiences = build_experiences(previous)
            if not experiences:
                continue
            previous_commit = str(previous.get("source_commit_at_execution") or "")
            current_commit = str(current.get("source_commit_at_execution") or "")
            distance = commit_distances.get((previous_commit, current_commit))
            decision = policy_decision(
                experiences[0],
                context,
                commit_distance=distance,
                threshold=threshold,
            )
            decisions.append({"trajectory_id": previous_id, **decision})
        policy_windows.append({**window, "policy_decisions": decisions})
    return {
        **replay,
        "protocol": "v3-chronological-policy-replay-v1",
        "policy": "deterministic_reliability_compatibility_commit_distance",
        "threshold": threshold,
        "windows": policy_windows,
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON at line {line_number}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"line {line_number} is not an object")
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trajectories", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifact = build_replay(load_jsonl(args.trajectories))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"protocol": artifact["protocol"], "rows": artifact["rows"]}))


if __name__ == "__main__":
    main()
