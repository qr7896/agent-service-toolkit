"""Playbook Stage-A gate: inventory, legacy integrity, and workspace identity."""

from __future__ import annotations

import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_legacy_artifact_seal import OUT as LEGACY_SEAL
from evals.e1c_strict_v5_legacy_artifact_seal import verify as verify_legacy
from evals.e1c_strict_v5_workspace_snapshot import OUT as WORKSPACE_SNAPSHOT
from evals.e1c_strict_v5_workspace_snapshot import verify as verify_workspace

CONTAMINATION = ROOT / "data" / "e1c_strict_v5_contamination_ledger.json"
OUT = ROOT / "data" / "e1c_strict_v5_stage_a_gate.json"


def _read(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build(output: Path = OUT) -> dict:
    workspace = _read(WORKSPACE_SNAPSHOT)
    legacy = _read(LEGACY_SEAL)
    contamination = _read(CONTAMINATION)
    workspace_check = (
        verify_workspace(WORKSPACE_SNAPSHOT) if workspace is not None else None
    )
    legacy_check = verify_legacy(LEGACY_SEAL) if legacy is not None else None
    checks = {
        "workspace_snapshot_present": workspace is not None,
        "workspace_snapshot_current": bool(workspace_check)
        and workspace_check.get("match") is True,
        "workspace_identity_explicit": bool(workspace)
        and isinstance(workspace.get("identity_sha256"), str)
        and workspace.get("workspace_identity_required") is True,
        "head_not_used_as_dirty_workspace_identity": bool(workspace)
        and workspace.get("head_is_sufficient_identity") is False,
        "legacy_seal_present": legacy is not None,
        "legacy_artifacts_unchanged": bool(legacy_check)
        and legacy_check.get("match") is True,
        "legacy_results_not_authoritative_for_v5": bool(legacy)
        and legacy.get("legacy_results_authoritative_for_v5") is False,
        "contamination_ledger_present": contamination is not None,
        "contamination_ledger_zero_provider": bool(contamination)
        and contamination.get("provider_calls") == 0,
        "contamination_ledger_new_tree_untouched": bool(contamination)
        and contamination.get("new_task_tree_touched") is False,
    }
    ready = all(checks.values())
    result = {
        "schema": "e1c-strict-v5-stage-a-gate-v1",
        "stage_a_ready": ready,
        "reason": (
            "stage_a_inventory_and_integrity_ready"
            if ready
            else "stage_a_inventory_or_integrity_incomplete"
        ),
        "checks": checks,
        "workspace_identity_sha256": (
            workspace.get("identity_sha256") if isinstance(workspace, dict) else None
        ),
        "workspace_identity_file_count": (
            workspace.get("identity_file_count") if isinstance(workspace, dict) else None
        ),
        "legacy_artifact_seal_sha256": (
            legacy.get("seal_sha256") if isinstance(legacy, dict) else None
        ),
        "legacy_sealed_file_count": (
            legacy.get("sealed_file_count") if isinstance(legacy, dict) else None
        ),
        "contamination_identity_count": (
            contamination.get("unique_identity_count")
            if isinstance(contamination, dict)
            else None
        ),
        "provider_calls": 0,
        "live_model_run": False,
        "live_allowed": False,
        "canary_allowed": False,
        "c5_allowed": False,
        "fresh30_allowed": False,
        "stage_a_ready_does_not_imply_live_admission": True,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
