"""Development-only replay of strict-v7 on already exposed strict-v6 material.

This is not independent evidence and must never open C5/DEV30/Fresh30 gates.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v7_probe import freeze_typed_plan

SOURCE = ROOT / "data" / "e1c_strict_v6_postfreeze_assessment.json"
OUT = ROOT / "data" / "e1c_strict_v7_dev_replay.json"


def build(source: Path = SOURCE) -> dict:
    document = json.loads(source.read_text(encoding="utf-8"))
    rows = []
    for old in document.get("rows", []):
        bundle = old.get("bundle") or {}
        issue = bundle.get("issue")
        localization = bundle.get("localization")
        if not isinstance(issue, str) or not isinstance(localization, dict):
            continue
        plan = freeze_typed_plan(issue, localization)
        rows.append(
            {
                "instance_id": old.get("instance_id"),
                "v6_witness_status": old.get("witness_status"),
                "v7_status": plan["status"],
                "candidate_count": plan["candidate_count"],
                "executable_candidate_count": plan["executable_candidate_count"],
                "candidate_kinds": [
                    row.get("freeze", {}).get("witness", {}).get("kind")
                    for row in plan["typed_candidates"]
                ],
                "plan": plan,
            }
        )
    executable_tasks = sum(row["executable_candidate_count"] > 0 for row in rows)
    typed_tasks = sum(row["candidate_count"] > 0 for row in rows)
    value = {
        "schema": "e1c-strict-v7-development-replay-v1",
        "provider_calls": 0,
        "live_model_run": False,
        "independent_evidence": False,
        "source_lineage": "sealed_strict_v6_exposed_material_only",
        "may_open_c5": False,
        "may_open_dev30": False,
        "may_open_fresh30": False,
        "task_count": len(rows),
        "typed_candidate_task_count": typed_tasks,
        "executable_candidate_task_count": executable_tasks,
        "rows": rows,
    }
    value["summary_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value


def main() -> None:
    value = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "task_count": value["task_count"],
                "typed_candidate_task_count": value["typed_candidate_task_count"],
                "executable_candidate_task_count": value["executable_candidate_task_count"],
                "provider_calls": value["provider_calls"],
                "independent_evidence": value["independent_evidence"],
                "summary_sha256": value["summary_sha256"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
