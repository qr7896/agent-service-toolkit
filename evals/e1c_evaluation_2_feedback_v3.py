"""Non-thinking DEV feedback contrast on the same two saved base-pass probes."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
from pathlib import Path

import httpx
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from agents.model_budget import _prompt_text, budgeted_ainvoke
from agents.model_router import estimate_tokens
from core.settings import settings
from evals.e1b_editor_adapter import content_text, usage_tokens
from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_dev_batch_v2 import _quote
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_feedback_v2 import _prompt, _selected, _source
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import execute_candidate, validate_candidate, verified_local_image

RUN_ID = "e1c2-dev-feedback-v3"
OUT = ROOT / ".codex/e1c/evaluation_2" / RUN_ID
FREEZE = OUT / "freeze.json"
LEDGER = OUT / "provider_calls.jsonl"
MAX_OUTPUT_TOKENS = 1800
TASK_TOKEN_CAP = 12_000
BATCH_TOKEN_CAP = 30_000


def preflight() -> dict:
    rows = []
    for instance_id, frozen, _, previous_source in _selected():
        prompt = _prompt(frozen, previous_source)
        reserve = math.ceil(estimate_tokens(_prompt_text([HumanMessage(content=prompt)])) * 1.4) + MAX_OUTPUT_TOKENS
        if reserve > TASK_TOKEN_CAP:
            raise ValueError("feedback prompt exceeds per-task reserve")
        rows.append({
            "instance_id": instance_id,
            "input_sha256": _sha(ISSUE / instance_id / "frozen_input_v3.json"),
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "image_id": verified_local_image(instance_id), "estimated_reserve": reserve,
        })
    total = sum(row["estimated_reserve"] for row in rows)
    if total > BATCH_TOKEN_CAP:
        raise ValueError("feedback batch reserve exceeds cap")
    return {
        "schema": "e1c2-dev-feedback-v3-freeze", "run_id": RUN_ID, "tasks": rows,
        "selection": "same_two_saved_prior_base_pass_DEV_candidates_as_v2",
        "model": "deepseek-flash", "thinking": "disabled", "sdk_retries": 0,
        "max_provider_calls": len(rows), "max_output_tokens_per_call": MAX_OUTPUT_TOKENS,
        "per_task_token_cap": TASK_TOKEN_CAP, "batch_token_cap": BATCH_TOKEN_CAP,
        "total_reserve": total, "elastic_token_ceiling": min(BATCH_TOKEN_CAP, math.ceil(total * 1.25)),
        "runner_sha256": _sha(Path(__file__)),
        "feedback_prompt_module_sha256": _sha(ROOT / "evals/e1c_evaluation_2_feedback_v2.py"),
        "probe_sha256": _sha(ROOT / "evals/e1c_evaluation_2_probe.py"), "provider_calls": 0,
    }


async def run() -> dict:
    if not FREEZE.is_file() or json.loads(FREEZE.read_text(encoding="utf-8")) != preflight():
        raise ValueError("feedback freeze missing or changed")
    if LEDGER.exists() or (OUT / "state.json").exists():
        raise FileExistsError("feedback identity already started; no auto-retry")
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek credential unavailable")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    state = {"run_id": RUN_ID, "status": "running", "rows": [], "trusted_reproducer_count": 0}
    _save(OUT / "state.json", state)
    async with httpx.AsyncClient(trust_env=False, timeout=90) as client:
        model = ChatOpenAI(
            model="deepseek-flash", temperature=0, streaming=False,
            openai_api_base="https://api.deepseek.com", openai_api_key=settings.DEEPSEEK_API_KEY,
            max_retries=0, http_async_client=client,
        )
        try:
            for row, (_, frozen, _, previous_source) in zip(freeze["tasks"], _selected(), strict=True):
                instance_id = row["instance_id"]
                response = await budgeted_ainvoke(
                    model, [HumanMessage(content=_prompt(frozen, previous_source))],
                    {"configurable": {
                        "provider_ledger_path": str(LEDGER), "provider_run_id": RUN_ID,
                        "provider_task_id": instance_id,
                        "provider_total_token_ceiling": freeze["elastic_token_ceiling"],
                        "provider_task_token_ceiling": TASK_TOKEN_CAP,
                        "provider_max_calls_per_task": 1,
                        "provider_max_output_tokens": MAX_OUTPUT_TOKENS,
                        "provider_prompt_reserve_multiplier": 1.4,
                        "provider_disable_thinking": True,
                    }}, role="e1c2_public_issue_feedback_nonthinking_v3",
                )
                raw = content_text(response)
                destination = OUT / instance_id
                _save(destination / "response.json", {
                    "prompt_sha256": row["prompt_sha256"], "raw": raw, "usage": usage_tokens(response),
                })
                status = {"instance_id": instance_id, "status": "response_saved"}
                try:
                    candidate = validate_candidate(
                        _source(raw), _quote(frozen), frozen, workspace=SOURCE / instance_id,
                    )
                    _save(destination / "candidate.json", candidate)
                    execution = execute_candidate(
                        candidate, row["image_id"], frozen["base_commit"], destination / "execution",
                        repeat_nonsetup_failure=True,
                    )
                    _save(destination / "execution.json", execution)
                    status.update({
                        "status": "executed",
                        "repeatable_failure_candidate": execution["repeatable_failure_candidate"],
                        "repeatable_nonsetup_failure": execution["repeatable_nonsetup_failure"],
                        "reasons": [item["reason"] for item in execution["runs"]],
                    })
                except (ValueError, SyntaxError, TypeError) as exc:
                    status.update({"status": "candidate_rejected", "reason": f"{type(exc).__name__}: {exc}"})
                state["rows"].append(status)
                (OUT / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(json.dumps(status, ensure_ascii=False), flush=True)
        except Exception as exc:
            state.update({"status": "interrupted_no_auto_retry", "error": f"{type(exc).__name__}: {exc}"})
            (OUT / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            raise
    state["status"] = "completed"
    (OUT / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": state["status"], "attempted": len(state["rows"]), "trusted_reproducer_count": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run"))
    args = parser.parse_args()
    if args.command == "preflight":
        value = preflight()
        if FREEZE.is_file():
            if json.loads(FREEZE.read_text(encoding="utf-8")) != value:
                raise ValueError("existing feedback freeze differs")
        else:
            _save(FREEZE, value)
        print(json.dumps({key: value[key] for key in (
            "model", "thinking", "max_provider_calls", "total_reserve", "elastic_token_ceiling",
        )}, ensure_ascii=False))
    else:
        print(json.dumps(asyncio.run(run()), ensure_ascii=False))


if __name__ == "__main__":
    main()
