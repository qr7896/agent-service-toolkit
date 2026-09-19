from __future__ import annotations

import argparse
import json
from pathlib import Path

from agents.experience import build_experiences


def load_trajectories(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid trajectory JSON at line {line_number}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"trajectory line {line_number} is not an object")
        rows.append(row)
    return rows


def export(trajectory_path: Path, output_path: Path, root: Path | None = None) -> dict:
    rows = load_trajectories(trajectory_path)
    compiled = []
    skipped = []
    for row in rows:
        experiences = build_experiences(row, root)
        if not experiences:
            skipped.append(str(row.get("id") or ""))
            continue
        for experience in experiences:
            compiled.append(
                {
                    "id": experience.id,
                    "trajectory_id": experience.trajectory_id,
                    "created_at": experience.created_at,
                    "task": experience.task,
                    "task_key": experience.task_key,
                    "outcome": experience.outcome,
                    "failure_type": experience.failure_type,
                    "effective_steps": experience.effective_steps,
                    "tools_used": experience.tools_used,
                    "changed_paths": experience.changed_paths,
                    "attempts": experience.attempts,
                    "test_summary": experience.test_summary,
                    "review_summary": experience.review_summary,
                    "approved": experience.approved,
                    "model": experience.model,
                    "duration_seconds": experience.duration_seconds,
                    "extra": experience.extra,
                }
            )
    artifact = {
        "protocol": "v3-experience-export-v1",
        "source": str(trajectory_path),
        "rows_seen": len(rows),
        "rows_compiled": len(compiled),
        "rows_skipped": len(skipped),
        "skipped_trajectory_ids": skipped,
        "experiences": compiled,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trajectories", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    artifact = export(args.trajectories, args.output, args.root)
    print(json.dumps({key: value for key, value in artifact.items() if key != "experiences"}))


if __name__ == "__main__":
    main()
