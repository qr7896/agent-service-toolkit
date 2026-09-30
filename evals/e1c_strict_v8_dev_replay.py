"""Development-only strict-v8 replay on already exposed v6/v7 material."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v6_runtime import build_bundle
from evals.e1c_strict_v8_probe import candidate_plan
from evals.e1c_strict_v8_source_contract import evaluate_source_effect, evaluate_source_usage

V6 = ROOT / "data" / "e1c_strict_v6_postfreeze_assessment.json"
V7 = ROOT / "data" / "e1c_strict_v7_postfreeze_assessment.json"
OUT = ROOT / "data" / "e1c_strict_v8_dev_replay.json"


def _source_root(statement_path: str) -> Path:
    return ROOT / Path(statement_path).parent / "source"


def _evaluate_source_candidates(plan: dict, workspace: Path) -> list[dict]:
    rows = []
    for candidate in plan.get("candidates", []):
        witness = candidate.get("witness") or {}
        kind = witness.get("kind")
        if kind == "source_usage":
            result = evaluate_source_usage(workspace, witness)
        elif kind == "source_effect":
            result = evaluate_source_effect(workspace, witness)
        else:
            continue
        rows.append(
            {
                "witness_sha256": witness.get("witness_sha256"),
                "origin": candidate.get("origin"),
                "result": result,
            }
        )
    return rows


def _v6_rows() -> list[dict]:
    document = json.loads(V6.read_text(encoding="utf-8"))
    rows = []
    for old in document.get("rows", []):
        bundle = old.get("bundle") or {}
        issue = bundle.get("issue")
        localization = bundle.get("localization")
        if not isinstance(issue, str) or not isinstance(localization, dict):
            continue
        plan = candidate_plan(issue, localization)
        workspace = _source_root(old["statement_path"])
        rows.append(
            {
                "lineage": "strict_v6_exposed",
                "instance_id": old["instance_id"],
                "candidate_count": plan["candidate_count"],
                "executable_candidate_count": plan["executable_candidate_count"],
                "source_results": _evaluate_source_candidates(plan, workspace),
                "plan": plan,
            }
        )
    return rows


def _v7_rows() -> list[dict]:
    document = json.loads(V7.read_text(encoding="utf-8"))
    rows = []
    for old in document.get("rows", []):
        statement_path = ROOT / old["statement_path"]
        workspace = _source_root(old["statement_path"])
        statement = statement_path.read_text(encoding="utf-8")
        manifest = json.loads((ROOT / "data" / "e1c_strict_v7_canary_manifest.json").read_text(encoding="utf-8"))
        task = next(row for row in manifest["tasks"] if row["instance_id"] == old["instance_id"])
        bundle = build_bundle(
            statement=statement,
            workspace=workspace,
            base_commit=task["base_commit"],
            forbidden_values=(old["instance_id"], task["image"]),
        )
        plan = candidate_plan(bundle["issue"], bundle["localization"])
        rows.append(
            {
                "lineage": "strict_v7_exposed",
                "instance_id": old["instance_id"],
                "candidate_count": plan["candidate_count"],
                "executable_candidate_count": plan["executable_candidate_count"],
                "source_results": _evaluate_source_candidates(plan, workspace),
                "plan": plan,
            }
        )
    return rows


def build() -> dict:
    rows = _v6_rows() + _v7_rows()
    candidate_tasks = sum(row["candidate_count"] > 0 for row in rows)
    executable_tasks = sum(row["executable_candidate_count"] > 0 for row in rows)
    source_witness_tasks = sum(bool(row["source_results"]) for row in rows)
    source_base_fail_tasks = sum(
        any(result["result"]["passed"] is False for result in row["source_results"])
        for row in rows
    )
    value = {
        "schema": "e1c-strict-v8-development-replay-v1",
        "provider_calls": 0,
        "live_model_run": False,
        "independent_evidence": False,
        "may_open_c5": False,
        "may_open_dev30": False,
        "may_open_fresh30": False,
        "task_count": len(rows),
        "candidate_task_count": candidate_tasks,
        "executable_candidate_task_count": executable_tasks,
        "source_witness_task_count": source_witness_tasks,
        "source_base_fail_task_count": source_base_fail_tasks,
        "rows": rows,
    }
    value["summary_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value


def main() -> None:
    value = build()
    OUT.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "task_count": value["task_count"],
        "candidate_task_count": value["candidate_task_count"],
        "executable_candidate_task_count": value["executable_candidate_task_count"],
        "source_witness_task_count": value["source_witness_task_count"],
        "source_base_fail_task_count": value["source_base_fail_task_count"],
        "independent_evidence": value["independent_evidence"],
        "summary_sha256": value["summary_sha256"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
