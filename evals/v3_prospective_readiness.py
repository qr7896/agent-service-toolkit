from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

REQUIRED = (
    "id",
    "ended_at",
    "source_repo",
    "source_commit_at_execution",
    "task",
    "changed_paths",
    "status",
)


def validate_row(row: dict[str, Any]) -> list[str]:
    errors = [f"missing:{key}" for key in REQUIRED if row.get(key) in (None, "")]
    if not isinstance(row.get("changed_paths"), list):
        errors.append("invalid:changed_paths")
    try:
        event = datetime.fromisoformat(str(row.get("ended_at") or "").replace("Z", "+00:00"))
        if event.tzinfo is None:
            errors.append("invalid:ended_at_timezone")
    except ValueError:
        errors.append("invalid:ended_at")
    if row.get("experience_hits") and "experience_ids" not in row:
        errors.append("missing:retrieved_experience_ids")
    if "experience_ids" in row and not isinstance(row.get("experience_ids"), list):
        errors.append("invalid:retrieved_experience_ids")
    if "adoption_observed" not in row:
        errors.append("missing:adoption_observation_state")
    elif row.get("adoption_observed") is True and not isinstance(
        row.get("adopted_experience_ids"), list
    ):
        errors.append("invalid:adopted_experience_ids")
    elif row.get("adoption_observed") is False and row.get("adopted_experience_ids") is not None:
        errors.append("invalid:unobserved_adoption_must_be_null")
    if row.get("adoption_observed") is True and isinstance(row.get("adopted_experience_ids"), list):
        retrieved = set(row.get("experience_ids") or [])
        if not set(row["adopted_experience_ids"]).issubset(retrieved):
            errors.append("invalid:adopted_not_retrieved")
    if row.get("usage_feedback") and any(
        not item.get("event_time") for item in row["usage_feedback"]
    ):
        errors.append("invalid:untimestamped_usage_feedback")
    return sorted(set(errors))


def build_readiness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    details = [{"id": str(row.get("id") or ""), "errors": validate_row(row)} for row in rows]
    ready = sum(not item["errors"] for item in details)
    blockers = Counter(error for item in details for error in item["errors"])
    provenance_complete = sum(
        bool(row.get("source_repo") and row.get("source_commit_at_execution")) for row in rows
    )
    return {
        "protocol": "v3-prospective-readiness-v1",
        "rows": len(rows),
        "replay_ready_rows": ready,
        "blocked_rows": len(rows) - ready,
        "ready": ready == len(rows) and ready > 0,
        "provenance_complete_rows": provenance_complete,
        "provenance_completeness": round(provenance_complete / len(rows), 4) if rows else 0.0,
        "blocker_counts": dict(sorted(blockers.items())),
        "chronological_replay_minimum_met": ready >= 2,
        "ready_ids": [item["id"] for item in details if not item["errors"]],
        "blocked_ids": [item["id"] for item in details if item["errors"]],
        "eligible_rows": [row for row, item in zip(rows, details) if not item["errors"]],
        "blocked_rows_detail": [
            {"row": row, "errors": item["errors"]}
            for row, item in zip(rows, details)
            if item["errors"]
        ],
        "details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trajectories", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [
        json.loads(line)
        for line in args.trajectories.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    artifact = build_readiness(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {key: artifact[key] for key in ("rows", "replay_ready_rows", "blocked_rows", "ready")}
        )
    )


if __name__ == "__main__":
    main()
