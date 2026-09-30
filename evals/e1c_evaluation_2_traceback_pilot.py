"""One-call DEV probe pilot selected from public, explicit issue tracebacks."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

import httpx
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from agents.model_budget import _prompt_text, budgeted_ainvoke
from agents.model_router import estimate_tokens
from core.settings import settings
from evals.e1b_editor_adapter import content_text, usage_tokens
from evals.e1c_blind_boundary import BlindBoundaryViolation
from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_admission import OUT as ADMISSION
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import (
    execute_candidate,
    generation_views,
    validate_candidate,
    verified_local_image,
)
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

RUN_ID = "e1c2-dev-traceback-pilot-v1"
OUT = ROOT / ".codex/e1c/evaluation_2" / RUN_ID
FREEZE = OUT / "freeze.json"
LEDGER = OUT / "provider_calls.jsonl"
MAX_PROVIDER_TOKENS = 12_000
MAX_OUTPUT_TOKENS = 1_200


def _prompt(frozen: dict) -> str:
    prompt = generation_views(frozen)[0]["prompt"]
    prompt += (
        "\nAssert only the minimum behavior explicitly required by the public issue. "
        "Do not require exact error text, formatting, or incidental values unless the issue requires them. "
        "If no sound executable assertion follows from the issue, return "
        '{"abstain_reason": "brief reason"} instead.'
    )
    audit_repair_visible_payload(prompt)
    return prompt


def _selected_inputs() -> list[Path]:
    paths = []
    for path in sorted(ISSUE.glob("*/frozen_input_v3.json")):
        frozen = json.loads(path.read_text(encoding="utf-8"))
        if (
            frozen.get("schema") == "e1c-evaluation-2-probe-input-v3"
            and frozen.get("status") == "ready_for_generation"
            and "Traceback:" in frozen["issue"]
            and re.search(r"(?m)^\s*[A-Za-z]+Error:", frozen["issue"])
        ):
            paths.append(path)
    return paths


def preflight() -> dict:
    paths = _selected_inputs()
    if len(paths) != 1:
        raise ValueError(f"expected exactly one public-traceback DEV input, found {len(paths)}")
    path = paths[0]
    instance_id = path.parent.name
    frozen = json.loads(path.read_text(encoding="utf-8"))
    phase_paths = [ADMISSION / instance_id / f"{phase}.json" for phase in ("base", "gold")]
    phases = [json.loads(item.read_text(encoding="utf-8")) for item in phase_paths]
    if any(phase.get("phase_pass") is not True or phase.get("provider_calls") != 0 for phase in phases):
        raise ValueError("public-traceback DEV input lacks official Base-Fail/Gold-Pass admission")
    prompt = _prompt(frozen)
    reserve = math.ceil(estimate_tokens(_prompt_text([HumanMessage(content=prompt)])) * 1.4) + MAX_OUTPUT_TOKENS
    if reserve > MAX_PROVIDER_TOKENS:
        raise ValueError(f"provider reserve {reserve} exceeds frozen ceiling {MAX_PROVIDER_TOKENS}")
    elastic_ceiling = min(MAX_PROVIDER_TOKENS, math.ceil(reserve * 1.5))
    image_id = verified_local_image(instance_id)
    inspected = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image_id],
        capture_output=True, text=True, timeout=30, check=False,
    )
    if inspected.returncode or inspected.stdout.strip() != image_id:
        raise ValueError("frozen DEV image is not available in Docker Engine")
    return {
        "schema": "e1c2-dev-traceback-pilot-freeze-v1",
        "run_id": RUN_ID, "instance_id": instance_id,
        "input_sha256": _sha(path),
        "base_admission_sha256": _sha(phase_paths[0]),
        "gold_admission_sha256": _sha(phase_paths[1]),
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "probe_module_sha256": _sha(ROOT / "evals/e1c_evaluation_2_probe.py"),
        "runner_module_sha256": _sha(Path(__file__)),
        "image_id": image_id, "estimated_call_reserve": reserve,
        "elastic_provider_ceiling": elastic_ceiling,
        "selection": "unique_v3_public_issue_with_traceback_and_explicit_error",
        "model": "deepseek-flash", "thinking": "disabled", "sdk_retries": 0,
        "max_provider_calls": 1, "hard_provider_token_cap": MAX_PROVIDER_TOKENS,
        "max_output_tokens_per_call": MAX_OUTPUT_TOKENS, "provider_calls": 0,
    }


async def run() -> dict:
    if not FREEZE.is_file() or json.loads(FREEZE.read_text(encoding="utf-8")) != preflight():
        raise ValueError("pilot freeze missing or source/input changed")
    if LEDGER.exists() or (OUT / "state.json").exists():
        raise FileExistsError("pilot already started; never auto-retry provider calls")
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek API credential unavailable")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    instance_id = freeze["instance_id"]
    frozen = json.loads((ISSUE / instance_id / "frozen_input_v3.json").read_text(encoding="utf-8"))
    prompt = _prompt(frozen)
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
                model, [HumanMessage(content=prompt)],
                {"configurable": {
                    "provider_ledger_path": str(LEDGER), "provider_run_id": RUN_ID,
                    "provider_task_id": instance_id,
                    "provider_total_token_ceiling": freeze["elastic_provider_ceiling"],
                    "provider_task_token_ceiling": freeze["elastic_provider_ceiling"],
                    "provider_max_calls_per_task": 1,
                    "provider_max_output_tokens": MAX_OUTPUT_TOKENS,
                    "provider_prompt_reserve_multiplier": 1.4, "provider_disable_thinking": True,
                }}, role="e1c2_issue_only_traceback_probe_generator",
            )
        raw = content_text(response)
        _save(OUT / "response.json", {
            "prompt_sha256": freeze["prompt_sha256"], "raw": raw, "usage": usage_tokens(response),
        })
        value = json.loads(raw)
        if isinstance(value, dict) and set(value) == {"abstain_reason"}:
            state.update({"status": "abstained", "reason": str(value["abstain_reason"])[:300]})
        else:
            if not isinstance(value, dict) or set(value) != {"source", "issue_quote"}:
                raise ValueError("response must contain source/issue_quote or abstain_reason")
            candidate = validate_candidate(value["source"], value["issue_quote"], frozen, workspace=SOURCE / instance_id)
            _save(OUT / "candidate.json", candidate)
            execution = execute_candidate(candidate, freeze["image_id"], frozen["base_commit"], OUT / "execution")
            _save(OUT / "execution.json", execution)
            state.update({
                "status": "executed", "repeatable_failure_candidate": execution["repeatable_failure_candidate"],
                "reasons": [item["reason"] for item in execution["runs"]],
            })
    except (BlindBoundaryViolation, ValueError, SyntaxError) as exc:
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
                raise ValueError("existing freeze differs; no silent overwrite")
        else:
            _save(FREEZE, value)
        print(json.dumps({"ready": True, "instance_id": value["instance_id"],
                          "estimated_call_reserve": value["estimated_call_reserve"],
                          "max_provider_calls": 1, "elastic_provider_ceiling": value["elastic_provider_ceiling"],
                          "hard_provider_token_cap": MAX_PROVIDER_TOKENS}, ensure_ascii=False))
    else:
        value = asyncio.run(run())
        print(json.dumps(value, ensure_ascii=False))


if __name__ == "__main__":
    main()
