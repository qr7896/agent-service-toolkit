"""Strict-v5 zero-provider runner skeleton.

This module prepares assertion-blind repair-visible artifacts only. It intentionally
contains no provider/model invocation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_gate import c5_gate, canary_gate, fresh30_gate
from evals.e1c_strict_v5_runtime import build_bundle, inspect_candidate
from evals.e1c_strict_v5_selector import frozen_selector_identity, reserve_status

PREP_ROOT = ROOT / ".codex" / "e1c" / "strict-v5" / "prep-v1"


def static_preflight() -> dict:
    reserve = reserve_status()
    return {
        "schema": "e1c-strict-v5-runner-static-preflight-v1",
        "ready": reserve["ready"] and not PREP_ROOT.exists(),
        "reason": (
            "ready_for_strict_materialization"
            if reserve["ready"] and not PREP_ROOT.exists()
            else reserve["reason"] if not reserve["ready"] else "strict_v5_prep_already_exists"
        ),
        "provider_calls": 0,
        "new_task_tree_touched": False,
        "prep_absent": not PREP_ROOT.exists(),
        "reserve": reserve,
        "legacy_v4_result_authoritative": False,
    }


def prepare_fixture(
    *,
    instance_id: str,
    statement: str,
    workspace: Path,
    base_commit: str,
    output_dir: Path,
    forbidden_values: tuple[str, ...] = (),
) -> dict:
    bundle = build_bundle(
        statement=statement,
        workspace=workspace,
        base_commit=base_commit,
        forbidden_values=forbidden_values,
    )
    if not bundle["candidate_paths"]:
        return {
            "schema": "e1c-strict-v5-prepared-row-v1",
            "instance_id": instance_id,
            "status": "abstain",
            "reason": "no_production_candidate",
            "provider_calls": 0,
        }
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "bundle.json"
    path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "schema": "e1c-strict-v5-prepared-row-v1",
        "instance_id": instance_id,
        "status": "prepared",
        "candidate_count": len(bundle["candidate_paths"]),
        "bundle_path": path.as_posix(),
        "bundle_sha256": bundle["bundle_sha256"],
        "provider_calls": 0,
    }


def inspect_fixture(bundle_path: Path, workspace: Path, path: str, symbol: str | None = None) -> dict:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    return inspect_candidate(bundle, workspace, path, symbol)


def gate_snapshot() -> dict:
    return {
        "schema": "e1c-strict-v5-gate-snapshot-v1",
        "provider_calls": 0,
        "new_task_tree_touched": False,
        "canary": canary_gate(),
        "c5": c5_gate(),
        "fresh30": fresh30_gate(),
    }


def selector_snapshot() -> dict:
    return frozen_selector_identity()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "gates"))
    args = parser.parse_args()
    result = static_preflight() if args.command == "preflight" else gate_snapshot()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.command == "preflight" and not result["ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
