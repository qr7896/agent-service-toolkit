"""Fresh one-call DEV identity after v2.6 stopped before any provider request."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import subprocess
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from agents.model_budget import _prompt_text, budgeted_ainvoke
from agents.model_router import estimate_tokens
from evals.e1b_editor_adapter import content_text, usage_tokens
from evals.e1c_dev_v22 import _attempt, _model
from evals.e1c_dev_v26 import SYSTEM, TASK_ID, _payload, _row
from evals.e1c_live_runner import MANIFEST_SHA256, OUT, _save, _source

RUN_ID = "e1c-dev-v27-regression1-20260924"
RUN_DIR = OUT / RUN_ID
LEDGER = RUN_DIR / "provider_calls.jsonl"
CAP = 6000
OUTPUT = 2000


def _compact_payload(source: Path) -> dict:
    value = _payload(source)
    rel = value["excerpts"][0]["path"]
    lines = (source / rel).read_text(encoding="utf-8").splitlines()
    value["excerpts"] = [
        {"path": rel, "start_line": 33, "text": "\n".join(lines[32:38])},
        {"path": rel, "start_line": 1909, "text": "\n".join(lines[1908:1917])},
        {"path": rel, "start_line": 1988, "text": "\n".join(lines[1987:2037])},
    ]
    return value


def preflight() -> dict:
    source = _source(_row())
    value = _compact_payload(source)
    messages = [SystemMessage(content=SYSTEM), HumanMessage(content=json.dumps(value, ensure_ascii=False))]
    reserve = math.ceil(estimate_tokens(_prompt_text(messages)) * 1.3) + OUTPUT
    return {"run_id": RUN_ID, "ready": reserve <= CAP and not RUN_DIR.exists(),
            "run_dir_absent": not RUN_DIR.exists(), "reserve": reserve,
            "manifest_sha256": MANIFEST_SHA256, "max_calls": 1,
            "max_output_tokens": OUTPUT, "task_token_ceiling": CAP}


async def run() -> dict:
    gate = preflight()
    if not gate["ready"]:
        raise RuntimeError("v2.7 zero-call preflight failed")
    row = _row()
    source = _source(row)
    workspace = RUN_DIR / "workspaces" / TASK_ID
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    _save(RUN_DIR / "identity.json", {**gate, "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                       "model": "deepseek-flash", "sdk_retries": 0,
                                       "claim_boundary": "outcome-selected DEV; not held-out efficacy"})
    workspace.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(source), "worktree", "add", "--detach", str(workspace),
                    row["base_commit"]], check=True, capture_output=True, timeout=120)
    artifacts = RUN_DIR / "artifacts" / TASK_ID
    artifacts.mkdir(parents=True)
    value = _compact_payload(source)
    _save(artifacts / "payload.json", value)
    try:
        response = await budgeted_ainvoke(
            _model(), [SystemMessage(content=SYSTEM), HumanMessage(content=json.dumps(value, ensure_ascii=False))],
            {"configurable": {"provider_ledger_path": str(LEDGER), "provider_run_id": RUN_ID,
                              "provider_task_id": TASK_ID, "provider_total_token_ceiling": CAP,
                              "provider_task_token_ceiling": CAP, "provider_max_calls_per_task": 1,
                              "provider_max_output_tokens": OUTPUT, "provider_prompt_reserve_multiplier": 1.3,
                              "provider_disable_thinking": True}}, role="compact_editor")
        grade, failure = _attempt(TASK_ID, workspace, content_text(response), value, "final", artifacts)
        state = {"status": "completed", "run_id": RUN_ID, "instance_id": TASK_ID,
                 "usage": usage_tokens(response), "resolved": bool(grade["resolved"]),
                 "grade": grade, "failure": failure}
    except Exception as exc:
        state = {"status": "interrupted_no_auto_retry", "run_id": RUN_ID,
                 "error": f"{type(exc).__name__}: {exc}"}
        _save(RUN_DIR / "state.json", state)
        raise
    _save(RUN_DIR / "state.json", state)
    return {key: state[key] for key in ("status", "run_id", "instance_id", "usage", "resolved", "failure")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run"))
    args = parser.parse_args()
    print(json.dumps(preflight() if args.command == "preflight" else asyncio.run(run()),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
