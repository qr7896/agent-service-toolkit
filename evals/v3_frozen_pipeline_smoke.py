from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evals.v3_chronological_replay import build_replay
from evals.v3_counterfactual_replay import build_counterfactual_replay
from evals.v3_memory_ablation import build_ablation
from evals.v3_prospective_readiness import build_readiness


def run_frozen_pipeline(
    rows: list[dict[str, Any]], commit_distances: dict[tuple[str, str], int]
) -> dict[str, Any]:
    readiness = build_readiness(rows)
    if not readiness["ready"]:
        return {"protocol": "v3-frozen-pipeline-smoke-v1", "ready": False, "readiness": readiness}
    replay = build_replay(rows)
    ablation = build_ablation(rows, commit_distances)
    counterfactual = build_counterfactual_replay(rows)
    return {
        "protocol": "v3-frozen-pipeline-smoke-v1",
        "ready": True,
        "readiness": readiness,
        "replay": replay,
        "ablation": ablation,
        "counterfactual": counterfactual,
        "claim_boundary": "Pipeline connectivity only; no efficacy claim.",
        "synthetic": True,
        "protocol_manifest": {
            "trajectory_schema": "v3-trajectory-v1",
            "readiness": readiness["protocol"],
            "replay": replay["protocol"],
            "ablation": ablation["protocol"],
            "counterfactual": counterfactual["protocol"],
        },
    }


def run_real_pipeline(
    rows: list[dict[str, Any]],
    commit_distances: dict[tuple[str, str], int],
    collection: dict[str, Any],
    status: dict[str, Any],
) -> dict[str, Any]:
    if collection.get("protocol") != "v3-prospective-collection-v1":
        raise ValueError("unsupported collection protocol")
    if collection.get("sealed_test") is not False:
        raise ValueError("real evaluation requires an explicitly non-sealed collection")
    if status.get("collection_id") != collection.get("collection_id"):
        raise ValueError("collection status does not match manifest")
    if status.get("prospective_rows") != len(rows):
        raise ValueError("prospective row count does not match status")
    readiness = status.get("readiness") or {}
    if not readiness.get("ready"):
        raise ValueError("prospective status is not ready")
    if set(readiness.get("ready_ids") or []) != {str(row.get("id") or "") for row in rows}:
        raise ValueError("prospective row identities do not match status")

    artifact = run_frozen_pipeline(rows, commit_distances)
    artifact["protocol"] = "v3-frozen-real-evaluation-v1"
    artifact["synthetic"] = False
    artifact["claim_boundary"] = (
        "Real prospective replay and evidence-availability evaluation only; "
        "no causal memory efficacy claim."
    )
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trajectories", type=Path, required=True)
    parser.add_argument("--commit-distances", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--collection", type=Path)
    parser.add_argument("--status", type=Path)
    args = parser.parse_args()
    rows = [
        json.loads(line)
        for line in args.trajectories.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    distances = {
        (item["from"], item["to"]): int(item["distance"])
        for item in json.loads(args.commit_distances.read_text(encoding="utf-8"))
    }
    if bool(args.collection) != bool(args.status):
        parser.error("--collection and --status must be provided together")
    if args.collection:
        artifact = run_real_pipeline(
            rows,
            distances,
            json.loads(args.collection.read_text(encoding="utf-8")),
            json.loads(args.status.read_text(encoding="utf-8")),
        )
    else:
        artifact = run_frozen_pipeline(rows, distances)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ready": artifact["ready"], "synthetic": artifact.get("synthetic", True)}))


if __name__ == "__main__":
    main()
