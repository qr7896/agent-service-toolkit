"""Zero-call prompt and source-evidence preflight for the E1-C adapter."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from agents.model_budget import _prompt_text
from agents.model_router import estimate_tokens
from evals.e1c_admission import ROOT, TASKS
from evals.e1c_evidence import excerpts
from evals.v3_compact_pilot import SYSTEM

OUT = ROOT / ".codex" / "e1c"
TASK_CEILING = 4000


def payload(instance_id: str, source: Path, commit: str) -> dict:
    statement = (TASKS / instance_id / "problem_statement.md").read_text(encoding="utf-8")
    return {
        "task": statement,
        "source_commit": commit,
        "excerpts": excerpts(statement, source),
        "statement_sha256": hashlib.sha256(statement.encode("utf-8")).hexdigest(),
        "statement_truncated": False,
    }


def fit_payload(value: dict) -> dict:
    value = {**value, "excerpts": list(value["excerpts"])}
    original_statement = value["task"]
    while len(value["excerpts"]) > 1 and reserve(value) > TASK_CEILING:
        value["excerpts"].pop()
    if reserve(value) > TASK_CEILING and len(value["task"]) > 2500:
        value["task"] = value["task"][:2000] + "\n[statement middle omitted by frozen budget rule]\n" + value["task"][-500:]
        value["statement_truncated"] = True
    if reserve(value) > TASK_CEILING and value["statement_truncated"]:
        value["task"] = original_statement[:1700] + "\n[statement middle omitted by frozen budget rule]\n" + original_statement[-400:]
    while len(value["excerpts"]) > 1 and reserve(value) > TASK_CEILING:
        value["excerpts"].pop()
    return value


def reserve(value: dict, *, multiplier: float = 2.0, max_output: int = 600) -> int:
    messages = [
        SystemMessage(content=SYSTEM),
        HumanMessage(content=json.dumps(value, ensure_ascii=False)),
    ]
    return math.ceil(estimate_tokens(_prompt_text(messages)) * multiplier) + max_output


def source_rows() -> dict[str, dict]:
    sources = {}
    for name in ("source_inventory.json", "replacement_source_inventory.json"):
        path = OUT / name
        if not path.exists():
            continue
        for row in json.loads(path.read_text(encoding="utf-8"))["tasks"]:
            if row["instance_id"] in sources:
                raise ValueError(f"duplicate source identity: {row['instance_id']}")
            sources[row["instance_id"]] = row
    return sources


def check(manifest_path: Path = OUT / "candidate_manifest.json") -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources = source_rows()
    rows = []
    for row in manifest["tasks"]:
        instance_id = row["instance_id"]
        source = sources[instance_id]
        if not source["match"] or source["expected_base_commit"] != row["base_commit"]:
            raise ValueError(f"source identity mismatch: {instance_id}")
        # Inventories are machine-local; never reuse their absolute workspace_path
        # after a WebCodex/Linux checkout. Derive the checkout from frozen identity.
        workspace = OUT / "repos" / row["repo"].replace("/", "__") / row["base_commit"]
        if not workspace.is_dir():
            raise FileNotFoundError(f"source checkout missing: {workspace}")
        value = fit_payload(payload(instance_id, workspace, row["base_commit"]))
        first_reserve = reserve(value)
        escalation = {
            **value,
            "escalation": {"policy": "frozen_class_specific", "evidence": "x" * 1200},
        }
        escalation_reserve = reserve(escalation, multiplier=1.0, max_output=400)
        rows.append(
            {
                "instance_id": instance_id,
                "first_reserve": first_reserve,
                "escalation_reserve_proxy": escalation_reserve,
                "excerpt_paths": [item["path"] for item in value["excerpts"]],
                "statement_truncated": value["statement_truncated"],
                "ready": bool(value["excerpts"])
                and first_reserve <= TASK_CEILING
                and escalation_reserve <= TASK_CEILING,
            }
        )
    return {
        "schema": "e1c-live-zero-call-preflight-v1",
        "task_count": len(rows),
        "ready_count": sum(row["ready"] for row in rows),
        "max_first_reserve": max(row["first_reserve"] for row in rows),
        "max_escalation_reserve_proxy": max(row["escalation_reserve_proxy"] for row in rows),
        "provider_calls": 0,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=OUT / "candidate_manifest.json")
    args = parser.parse_args()
    result = check(args.manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["ready_count"] != result["task_count"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
