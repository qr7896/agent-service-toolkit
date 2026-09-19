from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def audit_artifacts(
    collection: dict[str, Any],
    status: dict[str, Any],
    frozen: dict[str, Any],
    *,
    require_real: bool = True,
) -> dict[str, Any]:
    blockers = []
    if collection.get("protocol") != "v3-prospective-collection-v1":
        blockers.append("collection_protocol")
    if collection.get("trajectory_schema") != "v3-trajectory-v1":
        blockers.append("trajectory_schema")
    if status.get("collection_id") != collection.get("collection_id"):
        blockers.append("collection_id_mismatch")
    if frozen.get("ready"):
        replay = frozen.get("replay", {})
        counterfactual = frozen.get("counterfactual", {})
        if not replay.get("strict_past_only"):
            blockers.append("past_only_missing")
        if not frozen.get("claim_boundary"):
            blockers.append("claim_boundary_missing")
        if "matched_ready_pairs" not in counterfactual:
            blockers.append("matched_ready_pairs_missing")
        manifest = frozen.get("protocol_manifest", {})
        expected = {
            "trajectory_schema": collection.get("trajectory_schema"),
            "readiness": frozen.get("readiness", {}).get("protocol"),
            "replay": replay.get("protocol"),
            "ablation": frozen.get("ablation", {}).get("protocol"),
            "counterfactual": counterfactual.get("protocol"),
        }
        if manifest != expected:
            blockers.append("protocol_manifest_mismatch")
    if require_real and frozen.get("synthetic") is not False:
        blockers.append("synthetic_not_real")
    return {
        "protocol": "v3-artifact-audit-v1",
        "passed": not blockers,
        "blockers": sorted(set(blockers)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", type=Path, required=True)
    parser.add_argument("--status", type=Path, required=True)
    parser.add_argument("--frozen", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-synthetic", action="store_true")
    args = parser.parse_args()
    def load(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))
    artifact = audit_artifacts(
        load(args.collection),
        load(args.status),
        load(args.frozen),
        require_real=not args.allow_synthetic,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(artifact))


if __name__ == "__main__":
    main()
