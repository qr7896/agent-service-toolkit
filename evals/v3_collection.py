from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evals.v3_prospective_readiness import build_readiness


def create_manifest(
    collection_id: str, trajectory_path: Path, output: Path, preflight_artifact: dict[str, Any]
) -> dict[str, Any]:
    if not preflight_artifact.get("ready_to_collect"):
        raise ValueError("preflight is not ready_to_collect")
    if str(trajectory_path) != str(preflight_artifact.get("trajectory_path") or ""):
        raise ValueError("trajectory path does not match preflight")
    artifact = {
        "protocol": "v3-prospective-collection-v1",
        "collection_id": collection_id,
        "start_time": datetime.now(UTC).isoformat(),
        "trajectory_schema": "v3-trajectory-v1",
        "trajectory_path": str(trajectory_path),
        "sealed_test": False,
        "preflight_snapshot": {
            "source_repo": preflight_artifact.get("source_repo", ""),
            "current_commit": preflight_artifact.get("current_commit", ""),
            "ready_to_collect": True,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return artifact


def prospective_rows(manifest: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    start = datetime.fromisoformat(str(manifest["start_time"]).replace("Z", "+00:00"))
    prospective = []
    for row in rows:
        value = str(row.get("ended_at") or "")
        try:
            ended = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            continue
        if ended.tzinfo is not None and ended >= start:
            prospective.append(row)
    return prospective


def collection_status(manifest: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    if manifest.get("protocol") != "v3-prospective-collection-v1":
        raise ValueError("unsupported collection protocol")
    for key in (
        "collection_id",
        "start_time",
        "trajectory_schema",
        "trajectory_path",
        "preflight_snapshot",
    ):
        if key not in manifest:
            raise ValueError(f"collection manifest missing {key}")
    if manifest["trajectory_schema"] != "v3-trajectory-v1":
        raise ValueError("unsupported trajectory schema")
    prospective = prospective_rows(manifest, rows)
    readiness = build_readiness(prospective)
    return {
        "protocol": "v3-prospective-collection-status-v1",
        "collection_id": manifest["collection_id"],
        "historical_rows_excluded": len(rows) - len(prospective),
        "prospective_rows": len(prospective),
        "readiness": readiness,
        "adoption_observed_rows": sum(row.get("adoption_observed") is True for row in prospective),
        "adoption_observation_coverage": round(
            sum(row.get("adoption_observed") is True for row in prospective) / len(prospective), 4
        )
        if prospective
        else 0.0,
    }


def preflight(trajectory_path: Path) -> dict[str, Any]:
    parent = trajectory_path.parent
    writable = parent.exists() and parent.is_dir() and os.access(parent, os.W_OK)
    try:
        repo = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.strip()
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5, check=True
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        repo, commit = "", ""
    blockers = []
    if not writable:
        blockers.append("trajectory_unwritable")
    if not repo or not commit:
        blockers.append("git_unavailable")
    if not callable(build_readiness):
        blockers.append("readiness_unavailable")
    ready = not blockers
    return {
        "protocol": "v3-prospective-preflight-v1",
        "trajectory_path": str(trajectory_path),
        "trajectory_parent_exists": parent.exists(),
        "trajectory_parent_writable": writable,
        "source_repo": repo,
        "execution_commit_available": bool(commit),
        "current_commit": commit,
        "readiness_importable": callable(build_readiness),
        "ready_to_collect": ready,
        "blockers": blockers,
        "note": "Read-only preflight; no trajectory is fabricated.",
    }


def _rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    start = sub.add_parser("start")
    start.add_argument("--collection-id", required=True)
    start.add_argument("--trajectories", type=Path, required=True)
    start.add_argument("--output", type=Path, required=True)
    start.add_argument("--preflight", type=Path, required=True)
    status = sub.add_parser("status")
    status.add_argument("--manifest", type=Path, required=True)
    status.add_argument("--output", type=Path, required=True)
    status.add_argument("--prospective-output", type=Path)
    check = sub.add_parser("preflight")
    check.add_argument("--trajectories", type=Path, required=True)
    check.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "start":
        artifact = create_manifest(
            args.collection_id,
            args.trajectories,
            args.output,
            json.loads(args.preflight.read_text(encoding="utf-8")),
        )
    elif args.command == "status":
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        rows = _rows(Path(manifest["trajectory_path"]))
        artifact = collection_status(manifest, rows)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.prospective_output:
            args.prospective_output.parent.mkdir(parents=True, exist_ok=True)
            selected = prospective_rows(manifest, rows)
            args.prospective_output.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in selected),
                encoding="utf-8",
            )
    else:
        artifact = preflight(args.trajectories)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(artifact, ensure_ascii=False))


if __name__ == "__main__":
    main()
