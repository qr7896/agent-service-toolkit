"""One-call stronger-model DEV contrast for the frozen public CLI-option issue."""

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
from evals.e1c_evaluation_2_feedback_v2 import _source
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_option_v4_pilot import OUT as PRIOR
from evals.e1c_evaluation_2_option_v4_pilot import _selected
from evals.e1c_evaluation_2_probe import (
    execute_candidate,
    input_json,
    validate_candidate,
    verified_local_image,
)
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

RUN_ID = "e1c2-dev-option-v5-pro"
OUT = ROOT / ".codex/e1c/evaluation_2" / RUN_ID
FREEZE = OUT / "freeze.json"
LEDGER = OUT / "provider_calls.jsonl"
MAX_OUTPUT_TOKENS = 2400
TOKEN_CAP = 14_000


def _prompt(frozen: dict) -> str:
    context = input_json({"issue": frozen["issue"], "windows": frozen["windows"]})
    if len(context) > 24_000:
        raise ValueError("public issue context too large")
    prompt = (
        "Write a standalone, top-level Python script that reproduces only behavior explicitly requested by the "
        "public issue below. It must execute when run directly and contain at least one Python `assert` checking "
        "the requested behavior; a pytest test function, printed result, or forced exception alone is insufficient. "
        "Use only imports from the shown production package, plus safe `warnings`, `json`, or `numpy` if needed. "
        "Never import `subprocess`, `sys`, `os`, test modules, or any other I/O helper. Do not invoke an existing "
        "test suite, install packages, edit production files, or access network. Use the exact public input or CLI "
        "option described in the issue, not a synthetic substitute. Return exactly one JSON object with a source "
        "key containing executable Python code, or one with an abstain_reason key if the evidence is insufficient. "
        "Use only public issue and production-source windows; no evaluation artifacts.\n" + context
    )
    audit_repair_visible_payload(prompt)
    return prompt


def preflight() -> dict:
    instance_id, frozen, path = _selected()
    prior = json.loads((PRIOR / "state.json").read_text(encoding="utf-8"))
    prior_freeze = json.loads((PRIOR / "freeze.json").read_text(encoding="utf-8"))
    if prior_freeze.get("instance_id") != instance_id or prior.get("status") != "candidate_rejected":
        raise ValueError("prior DEV contrast is not sealed as rejected")
    prompt = _prompt(frozen)
    reserve = math.ceil(estimate_tokens(_prompt_text([HumanMessage(content=prompt)])) * 1.4) + MAX_OUTPUT_TOKENS
    if reserve > TOKEN_CAP:
        raise ValueError("prompt reserve exceeds token cap")
    return {
        "schema": "e1c2-dev-option-v5-pro-freeze", "run_id": RUN_ID,
        "instance_id": instance_id, "selection": "same_public_DEV_option_as_v4_stricter_script_contract",
        "input_sha256": _sha(path), "prior_response_sha256": _sha(PRIOR / "response.json"),
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "image_id": verified_local_image(instance_id),
        "model": "deepseek-v4-pro", "thinking": "disabled", "sdk_retries": 0,
        "max_provider_calls": 1, "max_output_tokens": MAX_OUTPUT_TOKENS,
        "estimated_reserve": reserve, "provider_token_cap": TOKEN_CAP,
        "runner_sha256": _sha(Path(__file__)),
        "probe_sha256": _sha(ROOT / "evals/e1c_evaluation_2_probe.py"), "provider_calls": 0,
    }


async def run() -> dict:
    if not FREEZE.is_file() or json.loads(FREEZE.read_text(encoding="utf-8")) != preflight():
        raise ValueError("strong-model DEV freeze missing or changed")
    if LEDGER.exists() or (OUT / "state.json").exists():
        raise FileExistsError("strong-model DEV already started; no auto-retry")
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek credential unavailable")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    instance_id, frozen, _ = _selected()
    state = {"run_id": RUN_ID, "status": "running", "trusted_reproducer_count": 0}
    _save(OUT / "state.json", state)
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=120) as client:
            model = ChatOpenAI(
                model="deepseek-v4-pro", temperature=0, streaming=False,
                openai_api_base="https://api.deepseek.com", openai_api_key=settings.DEEPSEEK_API_KEY,
                max_retries=0, http_async_client=client,
            )
            response = await budgeted_ainvoke(
                model, [HumanMessage(content=_prompt(frozen))],
                {"configurable": {
                    "provider_ledger_path": str(LEDGER), "provider_run_id": RUN_ID,
                    "provider_task_id": instance_id, "provider_total_token_ceiling": TOKEN_CAP,
                    "provider_task_token_ceiling": TOKEN_CAP, "provider_max_calls_per_task": 1,
                    "provider_max_output_tokens": MAX_OUTPUT_TOKENS,
                    "provider_prompt_reserve_multiplier": 1.4, "provider_disable_thinking": True,
                }}, role="e1c2_public_cli_option_strict_pro_v5",
            )
        raw = content_text(response)
        _save(OUT / "response.json", {
            "prompt_sha256": freeze["prompt_sha256"], "raw": raw, "usage": usage_tokens(response),
        })
        state["status"] = "response_saved"
        try:
            candidate = validate_candidate(
                _source(raw), _quote(frozen), frozen, workspace=SOURCE / instance_id,
            )
            _save(OUT / "candidate.json", candidate)
            execution = execute_candidate(
                candidate, freeze["image_id"], frozen["base_commit"], OUT / "execution",
                repeat_nonsetup_failure=True,
            )
            _save(OUT / "execution.json", execution)
            state.update({
                "status": "executed", "repeatable_failure_candidate": execution["repeatable_failure_candidate"],
                "repeatable_nonsetup_failure": execution["repeatable_nonsetup_failure"],
                "reasons": [item["reason"] for item in execution["runs"]],
            })
        except (ValueError, SyntaxError, TypeError) as exc:
            state.update({"status": "candidate_rejected", "reason": f"{type(exc).__name__}: {exc}"})
    except Exception as exc:
        state.update({"status": "interrupted_no_auto_retry", "error": f"{type(exc).__name__}: {exc}"})
        (OUT / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise
    (OUT / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run"))
    args = parser.parse_args()
    if args.command == "preflight":
        value = preflight()
        if FREEZE.is_file():
            if json.loads(FREEZE.read_text(encoding="utf-8")) != value:
                raise ValueError("existing strong-model freeze differs")
        else:
            _save(FREEZE, value)
        print(json.dumps({key: value[key] for key in (
            "instance_id", "model", "max_provider_calls", "estimated_reserve", "provider_token_cap",
        )}, ensure_ascii=False))
    else:
        print(json.dumps(asyncio.run(run()), ensure_ascii=False))


if __name__ == "__main__":
    main()
