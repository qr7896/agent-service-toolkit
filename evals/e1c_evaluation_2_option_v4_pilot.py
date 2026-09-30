"""One-call DEV probe on the unique public CLI-option locator improvement."""

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
from evals.e1c_evaluation_2_admission import OUT as ADMISSION
from evals.e1c_evaluation_2_dev_batch_v2 import _quote
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_feedback_v2 import _source
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import (
    execute_candidate,
    input_json,
    validate_candidate,
    verified_local_image,
)
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

RUN_ID = "e1c2-dev-option-v4-pilot"
OUT = ROOT / ".codex/e1c/evaluation_2" / RUN_ID
FREEZE = OUT / "freeze.json"
LEDGER = OUT / "provider_calls.jsonl"
MAX_OUTPUT_TOKENS = 1800
TOKEN_CAP = 12_000


def _selected() -> tuple[str, dict, Path]:
    changed = []
    for path in sorted(ISSUE.glob("*/frozen_input_v4.json")):
        old = json.loads((path.parent / "frozen_input_v3.json").read_text(encoding="utf-8"))
        new = json.loads(path.read_text(encoding="utf-8"))
        if old["candidate_paths"] != new["candidate_paths"]:
            if "--" not in new["issue"]:
                raise ValueError("changed locator input has no public CLI option")
            changed.append((path.parent.name, new, path))
    if len(changed) != 1:
        raise ValueError(f"expected unique DEV CLI-option locator change, found {len(changed)}")
    return changed[0]


def _prompt(frozen: dict) -> str:
    context = input_json({"issue": frozen["issue"], "windows": frozen["windows"]})
    if len(context) > 24_000:
        raise ValueError("public issue context too large")
    prompt = (
        "Use only this public issue and production-source windows. Write a standalone executable Python "
        "probe that checks the exact CLI-option behavior requested by the issue. Use the literal option named "
        "in the issue; assert only its stated behavior. Return one JSON object with a source key containing "
        "complete Python code, or one with an abstain_reason key. No test files, evaluation artifacts, "
        "production edits, dependency installation, or network access.\n" + context
    )
    audit_repair_visible_payload(prompt)
    return prompt


def preflight() -> dict:
    instance_id, frozen, path = _selected()
    admissions = [ADMISSION / instance_id / f"{phase}.json" for phase in ("base", "gold")]
    if any(json.loads(item.read_text(encoding="utf-8")).get("phase_pass") is not True for item in admissions):
        raise ValueError("official Base/Gold admission unavailable")
    prompt = _prompt(frozen)
    reserve = math.ceil(estimate_tokens(_prompt_text([HumanMessage(content=prompt)])) * 1.4) + MAX_OUTPUT_TOKENS
    if reserve > TOKEN_CAP:
        raise ValueError("prompt reserve exceeds token cap")
    return {
        "schema": "e1c2-dev-option-v4-pilot-freeze", "run_id": RUN_ID,
        "instance_id": instance_id, "selection": "unique_exact_public_cli_option_locator_change",
        "input_sha256": _sha(path), "prior_input_sha256": _sha(path.parent / "frozen_input_v3.json"),
        "base_admission_sha256": _sha(admissions[0]), "gold_admission_sha256": _sha(admissions[1]),
        "image_id": verified_local_image(instance_id), "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "model": "deepseek-flash", "thinking": "disabled", "sdk_retries": 0,
        "max_provider_calls": 1, "max_output_tokens": MAX_OUTPUT_TOKENS,
        "estimated_reserve": reserve, "provider_token_cap": TOKEN_CAP,
        "runner_sha256": _sha(Path(__file__)),
        "probe_sha256": _sha(ROOT / "evals/e1c_evaluation_2_probe.py"), "provider_calls": 0,
    }


async def run() -> dict:
    if not FREEZE.is_file() or json.loads(FREEZE.read_text(encoding="utf-8")) != preflight():
        raise ValueError("option pilot freeze missing or changed")
    if LEDGER.exists() or (OUT / "state.json").exists():
        raise FileExistsError("option pilot already started; no auto-retry")
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek credential unavailable")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    instance_id, frozen, _ = _selected()
    state = {"run_id": RUN_ID, "status": "running", "trusted_reproducer_count": 0}
    _save(OUT / "state.json", state)
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=90) as client:
            model = ChatOpenAI(
                model="deepseek-flash", temperature=0, streaming=False,
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
                }}, role="e1c2_public_cli_option_probe_v4",
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
                raise ValueError("existing option pilot freeze differs")
        else:
            _save(FREEZE, value)
        print(json.dumps({key: value[key] for key in (
            "instance_id", "model", "max_provider_calls", "estimated_reserve", "provider_token_cap",
        )}, ensure_ascii=False))
    else:
        print(json.dumps(asyncio.run(run()), ensure_ascii=False))


if __name__ == "__main__":
    main()
