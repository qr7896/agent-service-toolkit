from __future__ import annotations

import argparse
import asyncio
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.experience import ExperienceStore
from agents.model_budget import budgeted_ainvoke
from agents.workspace import export_patch
from core import get_model
from evals.v3_compact_pilot import (
    SYSTEM,
    _apply_edits,
    _parse_edits,
    _payload,
    content_text,
    usage_tokens,
)
from evals.v3_pilot_runner import TASKS, _grade, _prepare
from schema.models import DeepseekModelName

RUN_ID = "v3-paired-memory-0375-001"
RUN_DIR = Path(".codex/v3/paired-0375/live-001")
LEDGER = RUN_DIR / "provider_calls.jsonl"
EXPERIENCES = Path(".codex/v3/compact-002/experience.db")
TOTAL_TOKEN_CEILING = 8000
TASK_TOKEN_CEILING = 4000
MAX_OUTPUT_TOKENS = 600


def _task(commit: str):
    return next(task for task in TASKS if task.base_commit == commit)


def _memory(experience_ids: list[str]) -> list[dict[str, Any]]:
    rows = []
    with ExperienceStore(EXPERIENCES) as store:
        for trajectory_id in experience_ids:
            exp = store.get(trajectory_id)
            if exp is None:
                raise ValueError(f"missing eligible experience: {trajectory_id}")
            rows.append(
                {
                    "trajectory_id": trajectory_id,
                    "task": exp.task,
                    "changed_paths": exp.changed_paths,
                    "test_summary": exp.test_summary,
                    "outcome": exp.outcome,
                }
            )
    return rows


async def run_arm(pair: dict[str, Any], arm: dict[str, Any]) -> dict[str, Any]:
    task = _task(pair["source_commit"])
    name = arm["name"]
    workspace = RUN_DIR / "workspaces" / name
    _prepare(workspace, task)
    before = _grade(task, workspace)
    if before["passed"]:
        raise RuntimeError(f"base unexpectedly passes: {name}")
    payload = _payload(task, workspace)
    memory = _memory(pair["eligible_experience_ids"]) if arm["memory_enabled"] else []
    payload["memory_condition"] = name
    payload["past_experience"] = memory
    messages = [
        SystemMessage(content=SYSTEM),
        HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
    ]
    config = {
        "configurable": {
            "provider_ledger_path": str(LEDGER),
            "provider_run_id": RUN_ID,
            "provider_task_id": f"{task.instance_id}:{name}",
            "provider_total_token_ceiling": TOTAL_TOKEN_CEILING,
            "provider_task_token_ceiling": TASK_TOKEN_CEILING,
            "provider_max_calls_per_task": 1,
            "provider_max_output_tokens": MAX_OUTPUT_TOKENS,
            "provider_prompt_reserve_multiplier": 2.0,
            "provider_disable_thinking": True,
        }
    }
    started = time.perf_counter()
    started_at = datetime.now(UTC).isoformat()
    response = await budgeted_ainvoke(
        get_model(DeepseekModelName.DEEPSEEK_FLASH), messages, config, role="paired_memory_editor"
    )
    raw = content_text(response)
    usage = usage_tokens(response)
    edits = _parse_edits(raw, {row["path"] for row in payload["excerpts"]})
    _apply_edits(workspace, edits)
    grade = _grade(task, workspace)
    patch = export_patch(workspace)
    artifact = RUN_DIR / "artifacts" / name
    artifact.mkdir(parents=True, exist_ok=True)
    (artifact / "response.txt").write_text(raw, encoding="utf-8")
    (artifact / "patch.diff").write_text(patch["patch"], encoding="utf-8")
    result = {
        "arm": name,
        "memory_enabled": arm["memory_enabled"],
        "source_commit": task.base_commit,
        "started_at": started_at,
        "success": bool(grade["passed"]),
        "grade_exit_code": grade["exit_code"],
        "provider_usage": usage,
        "changed_files": patch["changed_files"],
        "eligible_experience_ids": pair["eligible_experience_ids"],
        "adopted_experience_ids": pair["eligible_experience_ids"] if memory else [],
        "adoption_observed": True,
        "wall_time_ms": round((time.perf_counter() - started) * 1000, 1),
    }
    (artifact / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


async def run(manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pairs = manifest.get("pairs") or []
    if len(pairs) != 1:
        raise ValueError("expected exactly one matched pair")
    pair = pairs[0]
    results = []
    for arm in pair["arms"]:
        results.append(await run_arm(pair, arm))
    comparison = {
        "protocol": "v3-paired-memory-live-v1",
        "run_id": RUN_ID,
        "threshold": manifest["threshold"],
        "pair": pair,
        "results": results,
        "delta": {
            "success": int(results[1]["success"]) - int(results[0]["success"]),
            "provider_tokens": results[1]["provider_usage"]["total_tokens"]
            - results[0]["provider_usage"]["total_tokens"],
            "wall_time_ms": round(results[1]["wall_time_ms"] - results[0]["wall_time_ms"], 1),
        },
        "claim_boundary": "Single exploratory matched pair; descriptive evidence only, not a causal efficacy claim.",
    }
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    (RUN_DIR / "comparison.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return comparison


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(run(args.manifest)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
