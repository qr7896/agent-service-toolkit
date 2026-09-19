from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path


def _trajectories(path: Path) -> tuple[list[dict], int]:
    rows, errors = [], 0
    if not path.is_file():
        return rows, errors
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            errors += 1
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            errors += 1
    return rows, errors


def _compiler_eligible(row: dict) -> bool:
    status = str(row.get("status") or "")
    if status == "succeeded":
        return True
    if any(item.get("approved") is False for item in row.get("approvals") or []):
        return True
    test = row.get("test_result") or {}
    review = row.get("review") or {}
    return bool(
        (test and test.get("status") != "passed")
        or review.get("approved") is False
        or status == "failed"
    )


def _experiences(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    uri = path.resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in connection.execute(
                "SELECT trajectory_id, created_at, outcome, failure_type, extra FROM experiences"
            )
        ]


def audit(trajectory_path: Path, experience_db: Path) -> dict:
    trajectories, parse_errors = _trajectories(trajectory_path)
    experiences = _experiences(experience_db)
    extras = []
    for row in experiences:
        try:
            extras.append(json.loads(row.get("extra") or "{}"))
        except json.JSONDecodeError:
            extras.append({})
    eligible = sum(_compiler_eligible(row) for row in trajectories)
    required_extra = {
        "schema_version",
        "source_repo",
        "event_time",
        "task_signature",
        "reuse_constraints",
        "repo_commit",
        "likely_effective",
        "retrieval_count",
        "used_count",
        "helped_count",
        "harmful_count",
    }
    complete_experiences = sum(required_extra <= set(extra) for extra in extras)
    temporal_trajectories = sum(
        bool(row.get("source_commit") or row.get("repo_commit_at_start")) for row in trajectories
    )
    outcomes = Counter(str(row.get("outcome") or "unknown") for row in experiences)
    has_both_outcomes = outcomes["accepted"] > 0 and outcomes["rejected"] > 0
    return {
        "protocol": "v3-experience-readiness-v1",
        "trajectory_inventory": {
            "rows": len(trajectories),
            "parse_errors": parse_errors,
            "statuses": dict(
                sorted(Counter(str(row.get("status") or "unknown") for row in trajectories).items())
            ),
            "compiler_eligible": eligible,
            "with_original_commit_provenance": temporal_trajectories,
            "with_experience_hits": sum(bool(row.get("experience_hits")) for row in trajectories),
        },
        "experience_inventory": {
            "rows": len(experiences),
            "outcomes": dict(sorted(outcomes.items())),
            "schema_v2_complete_rows": complete_experiences,
            "missing_compiled_rows": max(0, eligible - len(experiences)),
        },
        "gates": {
            "inventory_valid": parse_errors == 0,
            "existing_compiler_reusable": eligible > 0,
            "schema_v2_ready": bool(experiences) and complete_experiences == len(experiences),
            "temporal_provenance_ready": bool(trajectories)
            and temporal_trajectories == len(trajectories),
            "positive_negative_memory_ready": has_both_outcomes,
            "continual_evaluation_ready": False,
        },
        "next_gate": "freeze experience schema v2 and capture source commit at trajectory creation",
        "claim_boundary": "Readiness audit only; no learned policy, causal value, or continual improvement is measured.",
        "model_api_calls": 0,
        "sealed_test_opened_or_called": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trajectories", type=Path, required=True)
    parser.add_argument("--experience-db", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.trajectories, args.experience_db)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
