from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from evals.v3_chronological_replay import load_jsonl
from evals.v3_memory_ablation import build_ablation
from evals.v3_pilot_runner import TASKS, _grade, _prepare

DEFAULT_THRESHOLD = 0.6
SENSITIVITY_THRESHOLDS = (0.30, 0.35, 0.375, 0.38, 0.40, 0.50, 0.60, 0.70)


def load_distances(path: Path) -> dict[tuple[str, str], int | None]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return {(str(r["from"]), str(r["to"])): r.get("distance") for r in rows}


def preflight(trajectories: Path, distances: Path) -> dict[str, Any]:
    rows = load_jsonl(trajectories)
    commit_distances = load_distances(distances)
    sensitivity = []
    for threshold in SENSITIVITY_THRESHOLDS:
        artifact = build_ablation(rows, commit_distances, threshold)
        sensitivity.append({"threshold": threshold, **artifact["summary"]})
    frozen = build_ablation(rows, commit_distances, DEFAULT_THRESHOLD)
    candidate_thresholds = [
        row["threshold"] for row in sensitivity
        if row["selected_total_by_arm"]["reliability_aware"] > 0
    ]
    return {
        "protocol": "v3-paired-memory-preflight-v1",
        "provider_calls": 0,
        "rows": len(rows),
        "default_threshold": DEFAULT_THRESHOLD,
        "default_reliability_selected": frozen["summary"]["selected_total_by_arm"]["reliability_aware"],
        "sensitivity": sensitivity,
        "experimental_candidate_thresholds": candidate_thresholds,
        "ready_for_default_threshold_pair": bool(frozen["summary"]["selected_total_by_arm"]["reliability_aware"]),
        "claim_boundary": "Offline eligibility/preflight only; no memory efficacy claim and no provider call.",
    }


def build_pair_manifest(
    trajectories: Path, distances: Path, *, threshold: float = 0.375
) -> dict[str, Any]:
    rows = load_jsonl(trajectories)
    commit_distances = load_distances(distances)
    artifact = build_ablation(rows, commit_distances, threshold)
    candidates = []
    for sample in artifact["samples"]:
        selected = sample["arms"]["reliability_aware"]
        if not selected:
            continue
        candidates.append(
            {
                "task_id": sample["trajectory_id"],
                "source_commit": next(
                    str(row.get("source_commit_at_execution") or "")
                    for row in rows
                    if str(row.get("id")) == sample["trajectory_id"]
                ),
                "threshold": threshold,
                "eligible_experience_ids": selected,
                "arms": [
                    {"name": "memory_off", "memory_enabled": False},
                    {"name": "memory_on", "memory_enabled": True},
                ],
                "invariants": {
                    "same_task": True,
                    "same_source_commit": True,
                    "same_model": True,
                    "same_token_ceiling": True,
                    "same_grader": True,
                    "strict_past_only": True,
                },
            }
        )
    return {
        "protocol": "v3-paired-memory-manifest-v1",
        "provider_calls": 0,
        "threshold": threshold,
        "pairs": candidates,
        "ready": bool(candidates),
        "claim_boundary": "Experimental manifest only; no provider call and no efficacy claim.",
    }


def prepare_pair_workspaces(manifest: dict[str, Any], root: Path) -> dict[str, Any]:
    by_commit = {task.base_commit: task for task in TASKS}
    prepared = []
    for pair in manifest.get("pairs") or []:
        task = by_commit.get(str(pair.get("source_commit") or ""))
        if task is None:
            raise ValueError(f"no pilot task for source commit: {pair.get('source_commit')}")
        arm_rows = []
        for arm in pair["arms"]:
            workspace = root / str(pair["task_id"]) / arm["name"]
            if workspace.exists():
                shutil.rmtree(workspace)
            _prepare(workspace, task)
            before = _grade(task, workspace)
            arm_rows.append({
                "name": arm["name"],
                "memory_enabled": arm["memory_enabled"],
                "workspace": str(workspace),
                "base_fails": not before["passed"],
                "base_exit_code": before["exit_code"],
            })
        prepared.append({
            "task_id": pair["task_id"],
            "source_commit": pair["source_commit"],
            "arms": arm_rows,
            "matched_base": all(row["base_fails"] for row in arm_rows),
        })
    return {
        "protocol": "v3-paired-memory-workspace-preflight-v1",
        "provider_calls": 0,
        "pairs": prepared,
        "ready": bool(prepared) and all(row["matched_base"] for row in prepared),
    }

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--trajectories", type=Path, required=True)
    parser.add_argument("--commit-distances", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pair-threshold", type=float)
    parser.add_argument("--prepare-workspaces", type=Path)
    args=parser.parse_args()
    base = (
        build_pair_manifest(args.trajectories, args.commit_distances, threshold=args.pair_threshold)
        if args.pair_threshold is not None
        else preflight(args.trajectories, args.commit_distances)
    )
    artifact = prepare_pair_workspaces(base, args.prepare_workspaces) if args.prepare_workspaces else base
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(artifact,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(artifact,ensure_ascii=False,indent=2))

if __name__ == "__main__":
    main()
