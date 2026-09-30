"""One-call-per-task issue-only DEV probe batch; no grader material reaches the model."""

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
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import (
    execute_candidate,
    input_json,
    validate_candidate,
    verified_local_image,
)
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

RUN_ID = "e1c2-dev-batch-v2"
TASKS = (
    "marshmallow-code__marshmallow-1164",
    "pytest-dev__pytest-7432",
    "pytest-dev__pytest-7985",
    "scikit-learn__scikit-learn-15086",
    "scikit-learn__scikit-learn-26289",
)
OUT = ROOT / ".codex/e1c/evaluation_2" / RUN_ID
FREEZE = OUT / "freeze.json"
LEDGER = OUT / "provider_calls.jsonl"
MAX_OUTPUT_TOKENS = 1800
TASK_TOKEN_CAP = 18_000
BATCH_TOKEN_CAP = 90_000


def _prompt(frozen: dict) -> str:
    context = input_json({"issue": frozen["issue"], "windows": frozen["windows"]})
    if len(context) > 24_000:
        raise ValueError("issue-only context too large")
    prompt = (
        "Using only the public issue and production-source windows below, write a standalone Python "
        "probe that imports production code and asserts behavior explicitly requested by the issue. "
        "Return a JSON object with exactly one key named source; its value must be complete executable "
        "Python source code, not a placeholder or explanation. If the issue does not support a sound "
        "probe, return a JSON object with exactly one key named abstain_reason. "
        "Do not read tests, reference patches, evaluation artifacts, or task IDs; do not edit production files, "
        "install packages, access network, force an exception, or assert behavior absent from the issue.\n"
        + context
    )
    audit_repair_visible_payload(prompt)
    return prompt


def _quote(frozen: dict) -> str:
    title = frozen["issue"].splitlines()[0].strip()
    if len(title) < 8 or title not in frozen["issue"]:
        raise ValueError("no public issue title for evidence quote")
    return title


def preflight() -> dict:
    rows = []
    for instance_id in TASKS:
        path = ISSUE / instance_id / "frozen_input_v3.json"
        frozen = json.loads(path.read_text(encoding="utf-8"))
        if frozen.get("schema") != "e1c-evaluation-2-probe-input-v3" or frozen.get("status") != "ready_for_generation":
            raise ValueError(f"DEV input unavailable: {instance_id}")
        quote = _quote(frozen)
        prompt = _prompt(frozen)
        reserve = math.ceil(estimate_tokens(_prompt_text([HumanMessage(content=prompt)])) * 1.4) + MAX_OUTPUT_TOKENS
        if reserve > TASK_TOKEN_CAP:
            raise ValueError(f"DEV prompt reserve exceeds per-task cap: {instance_id}")
        admissions = [ADMISSION / instance_id / f"{phase}.json" for phase in ("base", "gold")]
        if any(json.loads(item.read_text(encoding="utf-8")).get("phase_pass") is not True for item in admissions):
            raise ValueError(f"official admission unavailable: {instance_id}")
        rows.append({
            "instance_id": instance_id,
            "input_sha256": _sha(path), "quote_sha256": hashlib.sha256(quote.encode()).hexdigest(),
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "base_admission_sha256": _sha(admissions[0]), "gold_admission_sha256": _sha(admissions[1]),
            "image_id": verified_local_image(instance_id), "estimated_reserve": reserve,
        })
    total_reserve = sum(row["estimated_reserve"] for row in rows)
    if total_reserve > BATCH_TOKEN_CAP:
        raise ValueError("batch reserve exceeds hard cap")
    return {
        "schema": "e1c2-dev-batch-v2-freeze", "run_id": RUN_ID, "tasks": rows,
        "selection": "five_remaining_pre-admitted_DEV_tasks_fixed_before_results",
        "model": "deepseek-flash", "max_provider_calls": len(rows), "sdk_retries": 0,
        "max_output_tokens_per_call": MAX_OUTPUT_TOKENS, "per_task_token_cap": TASK_TOKEN_CAP,
        "total_reserve": total_reserve, "batch_token_cap": BATCH_TOKEN_CAP,
        "elastic_token_ceiling": min(BATCH_TOKEN_CAP, math.ceil(total_reserve * 1.25)),
        "probe_module_sha256": _sha(ROOT / "evals/e1c_evaluation_2_probe.py"),
        "runner_module_sha256": _sha(Path(__file__)), "provider_calls": 0,
    }


async def run() -> dict:
    if not FREEZE.is_file() or json.loads(FREEZE.read_text(encoding="utf-8")) != preflight():
        raise ValueError("DEV batch freeze missing or changed")
    if LEDGER.exists() or (OUT / "state.json").exists():
        raise FileExistsError("DEV batch already started; no retry")
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
            for row in freeze["tasks"]:
                instance_id = row["instance_id"]
                frozen = json.loads((ISSUE / instance_id / "frozen_input_v3.json").read_text(encoding="utf-8"))
                response = await budgeted_ainvoke(
                    model, [HumanMessage(content=_prompt(frozen))],
                    {"configurable": {
                        "provider_ledger_path": str(LEDGER), "provider_run_id": RUN_ID,
                        "provider_task_id": instance_id,
                        "provider_total_token_ceiling": freeze["elastic_token_ceiling"],
                        "provider_task_token_ceiling": TASK_TOKEN_CAP,
                        "provider_max_calls_per_task": 1,
                        "provider_max_output_tokens": MAX_OUTPUT_TOKENS,
                        "provider_prompt_reserve_multiplier": 1.4,
                        "provider_disable_thinking": True,
                    }}, role="e1c2_public_issue_probe_v2",
                )
                raw = content_text(response)
                destination = OUT / instance_id
                _save(destination / "response.json", {
                    "prompt_sha256": row["prompt_sha256"], "raw": raw, "usage": usage_tokens(response),
                })
                status = {"instance_id": instance_id, "status": "response_saved"}
                try:
                    value = json.loads(raw)
                    if not isinstance(value, dict) or set(value) != {"source"}:
                        raise ValueError("response is not one Python source field")
                    candidate = validate_candidate(
                        value["source"], _quote(frozen), frozen, workspace=SOURCE / instance_id,
                    )
                    _save(destination / "candidate.json", candidate)
                    execution = execute_candidate(
                        candidate, row["image_id"], frozen["base_commit"], destination / "execution",
                        repeat_nonsetup_failure=True,
                    )
                    _save(destination / "execution.json", execution)
                    status.update({
                        "status": "executed", "repeatable_failure_candidate": execution["repeatable_failure_candidate"],
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
                raise ValueError("existing DEV batch freeze differs")
        else:
            _save(FREEZE, value)
        print(json.dumps({key: value[key] for key in (
            "model", "max_provider_calls", "total_reserve", "elastic_token_ceiling", "batch_token_cap",
        )}, ensure_ascii=False))
    else:
        print(json.dumps(asyncio.run(run()), ensure_ascii=False))


if __name__ == "__main__":
    main()
