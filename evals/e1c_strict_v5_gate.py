"""Fail-closed gates for the strict-v5 canary -> DEV30 -> Fresh30 lineage."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT

STRICT_ROOT = ROOT / ".codex" / "e1c" / "strict-v5"
CANARY_RESULT = STRICT_ROOT / "canary-v1" / "result.json"
DEV30_RESULT = STRICT_ROOT / "dev30-v1" / "result.json"
FRESH30_IDENTITY = ROOT / "data" / "e1c_strict_v5_fresh30_manifest.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canary_gate() -> dict:
    if not CANARY_RESULT.is_file():
        return {
            "schema": "e1c-strict-v5-canary-gate-v1",
            "ready": False,
            "reason": "strict_v5_independent_canary_not_completed",
            "provider_calls": 0,
            "new_task_tree_touched": False,
        }
    result = json.loads(CANARY_RESULT.read_text(encoding="utf-8"))
    treatment_only = result.get("treatment_only_resolved", [])
    baseline_only = result.get("baseline_only_resolved", [])
    anomalies = result.get("identity_anomalies", [])
    ready = bool(treatment_only) and not baseline_only and not anomalies and result.get("status") == "completed"
    return {
        "schema": "e1c-strict-v5-canary-gate-v1",
        "ready": ready,
        "reason": "treatment_only_gain" if ready else "strict_v5_canary_stop_rule_not_met",
        "treatment_only_resolved": treatment_only,
        "baseline_only_resolved": baseline_only,
        "identity_anomalies": anomalies,
        "result_sha256": _sha(CANARY_RESULT),
        "new_task_tree_touched": False,
    }


def c5_gate() -> dict:
    upstream = canary_gate()
    if not upstream["ready"]:
        return {
            "schema": "e1c-strict-v5-c5-gate-v1",
            "ready": False,
            "reason": "strict_v5_canary_gate_closed",
            "canary": upstream,
            "new_task_tree_touched": False,
        }
    if not DEV30_RESULT.is_file():
        return {
            "schema": "e1c-strict-v5-c5-gate-v1",
            "ready": False,
            "reason": "strict_v5_dev30_not_completed",
            "new_task_tree_touched": False,
        }
    result = json.loads(DEV30_RESULT.read_text(encoding="utf-8"))
    rows = result.get("rows", [])
    attempted = len(rows)
    resolved = sum(bool(row.get("resolved")) for row in rows)
    anomalies = result.get("identity_anomalies", [])
    ready = attempted == 30 and resolved == 30 and not anomalies and result.get("status") == "completed"
    return {
        "schema": "e1c-strict-v5-c5-gate-v1",
        "ready": ready,
        "reason": "strict_v5_dev30_30_of_30" if ready else "strict_v5_dev30_not_30_of_30",
        "attempted": attempted,
        "resolved": resolved,
        "identity_anomalies": anomalies,
        "result_sha256": _sha(DEV30_RESULT),
        "new_task_tree_touched": False,
    }


def fresh30_gate() -> dict:
    upstream = c5_gate()
    if not upstream["ready"]:
        return {
            "schema": "e1c-strict-v5-fresh30-gate-v1",
            "ready": False,
            "reason": "strict_v5_c5_gate_closed",
            "c5": upstream,
            "new_task_tree_touched": False,
            "materialization_allowed": False,
        }
    return {
        "schema": "e1c-strict-v5-fresh30-gate-v1",
        "ready": True,
        "reason": "strict_v5_canary_and_dev30_passed",
        "new_task_tree_touched": FRESH30_IDENTITY.exists(),
        "materialization_allowed": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("canary-gate", "c5-gate", "fresh30-gate"))
    args = parser.parse_args()
    result = {
        "canary-gate": canary_gate,
        "c5-gate": c5_gate,
        "fresh30-gate": fresh30_gate,
    }[args.command]()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
