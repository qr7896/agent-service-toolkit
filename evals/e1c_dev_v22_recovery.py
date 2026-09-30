"""One-call recovery of the interrupted v2.2 DEV task under a separate identity."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from agents.model_budget import _prompt_text, budgeted_ainvoke
from evals.e1b_editor_adapter import content_text, usage_tokens
from evals.e1c_dev_v22 import SYSTEM, _attempt, _cohort, _model, _reserve
from evals.e1c_live_runner import OUT, _save, _source

PARENT = OUT / "e1c-dev-v22-noop18-812ee4bd"
RUN_ID = "e1c-dev-v22-recovery-django-15280-20260924"
RUN_DIR = OUT / RUN_ID
TASK_ID = "django__django-15280"
AMBIGUOUS_CALL_ID = "29ee74c6-f40d-4bac-8859-7b2f19a62019"
FIRST_CALL_ID = "6ba7f9d4-3f63-4406-8cb6-3c413bc2f525"
PARENT_FIRST_TOKENS = 1205
TASK_TOKEN_CEILING = 8000


def preflight() -> tuple[dict, dict, dict]:
    parent_state = json.loads((PARENT / "state.json").read_text(encoding="utf-8"))
    if (parent_state.get("interrupted_task") != TASK_ID
            or parent_state.get("stop_reason") != "task_interrupted_no_auto_retry"
            or len(parent_state["rows"]) != 17 or RUN_DIR.exists()):
        raise ValueError("parent interruption or fresh recovery identity changed")
    events = [json.loads(line) for line in (PARENT / "provider_calls.jsonl").read_text(
        encoding="utf-8").splitlines()]
    last = {event["call_id"]: event for event in events}
    first = last.get(FIRST_CALL_ID, {})
    ambiguous = last.get(AMBIGUOUS_CALL_ID, {})
    if (first.get("status") != "completed" or first.get("task_id") != TASK_ID
            or first.get("total_tokens") != PARENT_FIRST_TOKENS
            or ambiguous.get("status") != "ambiguous" or ambiguous.get("task_id") != TASK_ID):
        raise ValueError("parent provider ledger changed")
    old_artifacts = PARENT / "artifacts" / TASK_ID
    if json.loads((old_artifacts / "response.first.txt").read_text(encoding="utf-8")) != {"edits": []}:
        raise ValueError("parent first response was not a no-op")
    payload_path = old_artifacts / "payload.final.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    messages = [SystemMessage(content=SYSTEM), HumanMessage(content=json.dumps(payload, ensure_ascii=False))]
    prompt_sha = hashlib.sha256(_prompt_text(messages).encode()).hexdigest()
    reserve = _reserve(payload, second=True)
    if (prompt_sha != ambiguous.get("prompt_sha256") or reserve > TASK_TOKEN_CEILING - PARENT_FIRST_TOKENS):
        raise ValueError("recovery prompt or cumulative budget changed")
    row = _cohort()[-1]
    if row["instance_id"] != TASK_ID:
        raise ValueError("cohort order changed")
    source = _source(row)
    admission = OUT / "admission_v2" / TASK_ID
    base = json.loads((admission / "base.json").read_text(encoding="utf-8"))
    gold = json.loads((admission / "gold.json").read_text(encoding="utf-8"))
    digest = subprocess.check_output(
        ["docker", "image", "inspect", base["image"], "--format", "{{index .RepoDigests 0}}"],
        text=True,
    ).strip()
    if not (base["phase_pass"] and gold["phase_pass"]
            and digest == base["image_digest"] == gold["image_digest"]):
        raise ValueError("official image admission changed")
    gate = {"run_id": RUN_ID, "parent_run_id": PARENT.name, "task_id": TASK_ID,
            "parent_ambiguous_call_id": AMBIGUOUS_CALL_ID,
            "payload_sha256": hashlib.sha256(payload_path.read_bytes()).hexdigest(),
            "prompt_sha256": prompt_sha, "reserve": reserve,
            "parent_first_tokens": PARENT_FIRST_TOKENS,
            "remaining_task_ceiling": TASK_TOKEN_CEILING - PARENT_FIRST_TOKENS,
            "source_commit": row["base_commit"], "source_path": str(source),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "v22_runner_sha256": hashlib.sha256(Path(__file__).with_name("e1c_dev_v22.py").read_bytes()).hexdigest(),
            "claim_boundary": "separate one-call recovery; original v2.2 remains incomplete"}
    return gate, row, payload


async def run() -> dict:
    gate, row, payload = preflight()
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    _save(RUN_DIR / "identity.json", gate)
    workspace = RUN_DIR / "workspaces" / TASK_ID
    workspace.parent.mkdir(parents=True)
    subprocess.run(["git", "-C", gate["source_path"], "worktree", "add", "--detach",
                    str(workspace), row["base_commit"]], check=True, capture_output=True, timeout=120)
    artifacts = RUN_DIR / "artifacts" / TASK_ID
    artifacts.mkdir(parents=True)
    _save(artifacts / "payload.recovery.json", payload)
    messages = [SystemMessage(content=SYSTEM), HumanMessage(content=json.dumps(payload, ensure_ascii=False))]
    config = {"configurable": {
        "provider_ledger_path": str(RUN_DIR / "provider_calls.jsonl"),
        "provider_run_id": RUN_ID, "provider_task_id": TASK_ID,
        "provider_total_token_ceiling": gate["remaining_task_ceiling"],
        "provider_task_token_ceiling": gate["remaining_task_ceiling"],
        "provider_max_calls_per_task": 1, "provider_max_output_tokens": 400,
        "provider_prompt_reserve_multiplier": 1.0, "provider_disable_thinking": True,
    }}
    try:
        response = await budgeted_ainvoke(_model(), messages, config, role="compact_editor")
        grade, failure = _attempt(TASK_ID, workspace, content_text(response), payload, "recovery", artifacts)
        result = {"status": "completed", "run_id": RUN_ID, "task_id": TASK_ID,
                  "provider_usage": usage_tokens(response), "resolved": grade["resolved"],
                  "failure": failure, "grade": grade}
    except Exception as exc:
        result = {"status": "interrupted_no_auto_retry", "run_id": RUN_ID,
                  "task_id": TASK_ID, "error": f"{type(exc).__name__}: {exc}"}
        _save(RUN_DIR / "state.json", result)
        raise
    _save(RUN_DIR / "state.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run"))
    args = parser.parse_args()
    if args.command == "preflight":
        print(json.dumps(preflight()[0], ensure_ascii=False, indent=2))
    else:
        result = asyncio.run(run())
        print(json.dumps({key: result[key] for key in ("run_id", "status", "resolved", "provider_usage")},
                         ensure_ascii=False))


if __name__ == "__main__":
    main()
