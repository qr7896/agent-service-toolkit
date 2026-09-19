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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trajectories", type=Path, required=True)
    parser.add_argument("--commit-distances", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
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
    artifact = run_frozen_pipeline(rows, distances)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ready": artifact["ready"], "synthetic": artifact.get("synthetic", True)}))


if __name__ == "__main__":
    main()
