"""Fresh-30 gate for the frozen reproducer-v3 experiment lineage."""

from __future__ import annotations

import argparse
import hashlib
import json

from evals.e1c_admission import ROOT

REPRO_V3_CANARY_RUN = ROOT / ".codex" / "e1c" / "e1c-blind-reproducer-c4r-v3-v1"
FULL30_RUN = ROOT / ".codex" / "e1c" / "e1c-blind-reproducer-v3-c5-n30-v1"


def gate() -> dict:
    canary = REPRO_V3_CANARY_RUN / "result.json"
    if not canary.is_file():
        return {
            "schema": "e1c-fresh30-gate-v3",
            "ready": False,
            "reason": "reproducer_v3_canary_not_completed",
            "new_task_tree_touched": False,
        }
    canary_result = json.loads(canary.read_text(encoding="utf-8"))
    if canary_result.get("expand_c5") is not True:
        return {
            "schema": "e1c-fresh30-gate-v3",
            "ready": False,
            "reason": "reproducer_v3_canary_stop_rule_not_met",
            "new_task_tree_touched": False,
            "canary_sha256": hashlib.sha256(canary.read_bytes()).hexdigest(),
        }
    full = FULL30_RUN / "result.json"
    if not full.is_file():
        return {
            "schema": "e1c-fresh30-gate-v3",
            "ready": False,
            "reason": "C5_full30_not_completed",
            "new_task_tree_touched": False,
        }
    result = json.loads(full.read_text(encoding="utf-8"))
    rows = result.get("rows", [])
    resolved = sum(bool(row.get("resolved")) for row in rows)
    attempted = len(rows)
    ready = attempted == 30 and resolved == 30 and result.get("status") == "completed"
    return {
        "schema": "e1c-fresh30-gate-v3",
        "ready": ready,
        "reason": "C5_same_version_30_of_30" if ready else "C5_not_30_of_30",
        "attempted": attempted,
        "resolved": resolved,
        "new_task_tree_touched": False,
        "c5_sha256": hashlib.sha256(full.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("gate",))
    parser.parse_args()
    result = gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
