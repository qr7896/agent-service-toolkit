"""Assertion-blind E1-C runner: repair side never consumes benchmark oracle fields."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import subprocess
from functools import cache
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agents.model_budget import _prompt_text, budgeted_ainvoke
from agents.model_router import estimate_tokens
from core.settings import settings
from evals.e1b_editor_adapter import content_text, usage_tokens
from evals.e1c_admission import ROOT, TASKS
from evals.e1c_blind_boundary import assert_agent_payload, audit_serialized_agent_trace
from evals.e1c_docker_grade import grade
from evals.e1c_evidence_v2 import excerpts
from evals.e1c_live_runner import MANIFEST_SHA256, _manifest, _patch, _save, _source
from evals.v3_compact_pilot import _apply_edits, _parse_edits
from schema.models import DeepseekModelName

OUT = ROOT / ".codex" / "e1c"
RUN_ID = "e1c-blind-canary-v1"
RUN_DIR = OUT / RUN_ID
LEDGER = RUN_DIR / "provider_calls.jsonl"
MODEL = DeepseekModelName.DEEPSEEK_FLASH
CANARY_COUNT = 4
TASK_TOKEN_CEILING = 6000
TOTAL_TOKEN_CEILING = 48000
SYSTEM = """You are repairing a Python repository using only the public issue and bounded exact-base source excerpts.
Return JSON only: {"edits":[{"path":"relative/path","old":"exact existing text","new":"replacement text"}]}.
Use at most four minimal exact replacements. Paths must be among supplied excerpts. Never edit tests.
If evidence is insufficient, return {"edits":[]}. Do not assume hidden tests or benchmark grader details.
"""


def _statement(instance_id: str) -> str:
    return (TASKS / instance_id / "problem_statement.md").read_text(encoding="utf-8")


def blind_payload(row: dict, workspace: Path, *, structured: bool) -> dict:
    statement = _statement(row["instance_id"])
    evidence = excerpts(statement, workspace, max_files=4 if structured else 2, max_chars=1400)
    payload = {
        "issue": statement,
        "source_commit": row["base_commit"],
        "evidence_mode": "issue_structured_locator" if structured else "issue_lexical_baseline",
        "excerpts": [
            {
                **item,
                "source_sha256": hashlib.sha256(
                    (workspace / item["path"]).read_bytes()
                ).hexdigest(),
                "origin": "issue+exact_base",
                "rank": index + 1,
            }
            for index, item in enumerate(evidence)
        ],
    }
    assert_agent_payload(payload)
    audit_serialized_agent_trace(json.dumps(payload, ensure_ascii=False))
    return payload


def _reserve(payload: dict) -> int:
    messages = [SystemMessage(content=SYSTEM), HumanMessage(content=json.dumps(payload, ensure_ascii=False))]
    return math.ceil(estimate_tokens(_prompt_text(messages)) * 1.5) + 700


def _canary_rows() -> list[dict]:
    manifest = _manifest()
    rows = manifest["tasks"][:CANARY_COUNT]
    if len(rows) != CANARY_COUNT:
        raise ValueError("frozen manifest lacks canary rows")
    return rows


def preflight() -> dict:
    rows = []
    for row in _canary_rows():
        source = _source(row)
        for structured in (False, True):
            payload = blind_payload(row, source, structured=structured)
            rows.append({
                "instance_id": row["instance_id"],
                "arm": "structured" if structured else "baseline",
                "paths": [item["path"] for item in payload["excerpts"]],
                "reserve": _reserve(payload),
                "ready": bool(payload["excerpts"]) and _reserve(payload) <= TASK_TOKEN_CEILING,
            })
    return {
        "schema": "e1c-assertion-blind-canary-preflight-v1",
        "run_id": RUN_ID,
        "manifest_sha256": MANIFEST_SHA256,
        "canary_count": CANARY_COUNT,
        "provider_calls": 0,
        "artifacts_absent": not RUN_DIR.exists(),
        "rows": rows,
        "ready": len(rows) == CANARY_COUNT * 2 and all(row["ready"] for row in rows) and not RUN_DIR.exists(),
    }


@cache
def _model() -> ChatOpenAI:
    return ChatOpenAI(
        model=str(MODEL),
        temperature=0.5,
        streaming=True,
        openai_api_base="https://api.deepseek.com",
        openai_api_key=settings.DEEPSEEK_API_KEY,
        max_retries=0,
    )


def _config(task_id: str) -> dict:
    return {"configurable": {
        "provider_ledger_path": str(LEDGER),
        "provider_run_id": RUN_ID,
        "provider_task_id": task_id,
        "provider_total_token_ceiling": TOTAL_TOKEN_CEILING,
        "provider_task_token_ceiling": TASK_TOKEN_CEILING,
        "provider_max_calls_per_task": 2,
        "provider_max_output_tokens": 700,
        "provider_prompt_reserve_multiplier": 1.5,
        "provider_disable_thinking": True,
    }}


async def _call(task_id: str, payload: dict) -> tuple[str, dict]:
    response = await budgeted_ainvoke(
        _model(),
        [SystemMessage(content=SYSTEM), HumanMessage(content=json.dumps(payload, ensure_ascii=False))],
        _config(task_id),
        role="blind_editor",
    )
    return content_text(response), usage_tokens(response)


def _workspace(row: dict, arm: str) -> Path:
    source = _source(row)
    workspace = RUN_DIR / "workspaces" / arm / row["instance_id"]
    workspace.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-C", str(source), "worktree", "add", "--detach", str(workspace), row["base_commit"]],
        check=True, capture_output=True, timeout=120,
    )
    return workspace


async def _arm(row: dict, arm: str) -> dict:
    workspace = _workspace(row, arm)
    repair_dir = RUN_DIR / "repair" / arm / row["instance_id"]
    evaluator_dir = RUN_DIR / "evaluator" / arm / row["instance_id"]
    repair_dir.mkdir(parents=True)
    payload = blind_payload(row, workspace, structured=arm == "structured")
    _save(repair_dir / "payload.json", payload)
    raw, usage = await _call(f"{row['instance_id']}:{arm}", payload)
    (repair_dir / "response.txt").write_text(raw, encoding="utf-8")
    try:
        edits = _parse_edits(raw, {item["path"] for item in payload["excerpts"]})
        if not edits:
            return {"instance_id": row["instance_id"], "arm": arm, "resolved": False, "abstain": True, "usage": usage}
        _apply_edits(workspace, edits)
        patch = repair_dir / "candidate.diff"
        _patch(workspace, patch)
        if not patch.stat().st_size:
            return {"instance_id": row["instance_id"], "arm": arm, "resolved": False, "abstain": True, "usage": usage}
    except (json.JSONDecodeError, TypeError, ValueError, PermissionError, OSError) as exc:
        return {"instance_id": row["instance_id"], "arm": arm, "resolved": False, "patch_failure": f"{type(exc).__name__}: {exc}", "usage": usage}
    result = grade(row["instance_id"], arm, patch, evaluator_dir)
    return {"instance_id": row["instance_id"], "arm": arm, "resolved": result["resolved"], "abstain": False, "usage": usage}


async def run() -> dict:
    gate = preflight()
    if not gate["ready"]:
        raise RuntimeError(f"blind canary preflight not ready: {gate}")
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    _save(RUN_DIR / "identity.json", {
        **gate,
        "protocol": "e1c-assertion-blind-paired-canary-v1",
        "model": str(MODEL),
        "system_sha256": hashlib.sha256(SYSTEM.encode()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "stop_rule": "do_not_expand_if_structured_has_no_net_new_resolved_or_safety_budget_anomaly",
    })
    outcomes = []
    for row in _canary_rows():
        for arm in ("baseline", "structured"):
            outcome = await _arm(row, arm)
            outcomes.append(outcome)
            _save(RUN_DIR / "state.json", {"schema": "e1c-blind-canary-state-v1", "rows": outcomes})
    baseline = {r["instance_id"] for r in outcomes if r["arm"] == "baseline" and r["resolved"]}
    structured = {r["instance_id"] for r in outcomes if r["arm"] == "structured" and r["resolved"]}
    summary = {
        "schema": "e1c-blind-canary-result-v1",
        "rows": outcomes,
        "baseline_resolved": len(baseline),
        "structured_resolved": len(structured),
        "net_new_resolved": len(structured - baseline),
        "lost_resolved": len(baseline - structured),
        "expand_b5": bool(structured - baseline) and not (baseline - structured),
    }
    _save(RUN_DIR / "result.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run"))
    args = parser.parse_args()
    result = preflight() if args.command == "preflight" else asyncio.run(run())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.command == "preflight" and not result["ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
