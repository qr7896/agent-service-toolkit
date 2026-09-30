"""Fresh-30 gate: refuses to inspect/select new tasks until frozen C5 is exactly 30/30."""

from __future__ import annotations

import argparse
import hashlib
import json

from evals.e1c_admission import ROOT

POSTB4_RUN = ROOT / ".codex" / "e1c" / "e1c-blind-postb4-c4-v1"
FULL30_RUN = ROOT / ".codex" / "e1c" / "e1c-blind-postb4-c5-n30-v1"


def gate() -> dict:
    c4 = POSTB4_RUN / "result.json"
    if not c4.is_file():
        return {
            "schema": "e1c-fresh30-gate-v1",
            "ready": False,
            "reason": "C4_not_completed",
            "new_task_tree_touched": False,
        }
    c4_result = json.loads(c4.read_text(encoding="utf-8"))
    if c4_result.get("expand_c5") is not True:
        return {
            "schema": "e1c-fresh30-gate-v1",
            "ready": False,
            "reason": "C4_stop_rule_not_met",
            "new_task_tree_touched": False,
            "c4_sha256": hashlib.sha256(c4.read_bytes()).hexdigest(),
        }
    full = FULL30_RUN / "result.json"
    if not full.is_file():
        return {
            "schema": "e1c-fresh30-gate-v1",
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
        "schema": "e1c-fresh30-gate-v1",
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
