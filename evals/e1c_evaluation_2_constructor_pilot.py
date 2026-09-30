"""One-call, issue-only DEV probe for an explicit constructor-parameter request."""

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
from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_admission import OUT as ADMISSION
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_probe import input_json, verified_local_image
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

RUN_ID = "e1c2-dev-constructor-pilot-v1"
OUT = ROOT / ".codex/e1c/evaluation_2" / RUN_ID
FREEZE = OUT / "freeze.json"
LEDGER = OUT / "provider_calls.jsonl"
HARD_PROVIDER_TOKEN_CAP = 12_000
MAX_OUTPUT_TOKENS = 1_200
_REQUEST = re.compile(r"(?i)\bexpose\s+`[^`]+`\s+in\s+`[^`]+`,\s+default\s+`[^`]+`")


def _selected() -> tuple[Path, dict, str]:
    matches = []
    for path in sorted(ISSUE.glob("*/frozen_input_v3.json")):
        frozen = json.loads(path.read_text(encoding="utf-8"))
        if frozen.get("schema") != "e1c-evaluation-2-probe-input-v3" or frozen.get("status") != "ready_for_generation":
            continue
        requests = _REQUEST.findall(frozen["issue"])
        if len(requests) == 1:
            matches.append((path, frozen, requests[0]))
    if len(matches) != 1:
        raise ValueError(f"expected one explicit constructor-parameter DEV issue, found {len(matches)}")
    return matches[0]


def _prompt(frozen: dict) -> str:
    context = input_json({"issue": frozen["issue"], "windows": frozen["windows"]})
    if len(context) > 24_000:
        raise ValueError("issue-only context exceeds bounded prompt size")
    prompt = (
        "Use only this public issue and frozen production-source windows. Write one standalone Python probe "
        "with an explicit assert for the requested constructor behavior on unchanged base code. "
        "Test no more than the issue states; do not rely on exact incidental error wording. "
        "Do not read tests or evaluation artifacts, write production files, install packages, or use network. "
        'Return JSON only: {"source":"Python probe"}; if no sound probe is possible, '
        'return {"abstain_reason":"brief reason"}.\n' + context
    )
    audit_repair_visible_payload(prompt)
    return prompt


def preflight() -> dict:
    path, frozen, quote = _selected()
    instance_id = path.parent.name
    phase_paths = [ADMISSION / instance_id / f"{phase}.json" for phase in ("base", "gold")]
    phases = [json.loads(item.read_text(encoding="utf-8")) for item in phase_paths]
    if any(phase.get("phase_pass") is not True or phase.get("provider_calls") != 0 for phase in phases):
        raise ValueError("constructor DEV task lacks official Base-Fail/Gold-Pass admission")
    prompt = _prompt(frozen)
    reserve = math.ceil(estimate_tokens(_prompt_text([HumanMessage(content=prompt)])) * 1.4) + MAX_OUTPUT_TOKENS
    if reserve > HARD_PROVIDER_TOKEN_CAP:
        raise ValueError(f"provider reserve {reserve} exceeds hard cap {HARD_PROVIDER_TOKEN_CAP}")
    ceiling = min(HARD_PROVIDER_TOKEN_CAP, math.ceil(reserve * 1.5))
    image_id = verified_local_image(instance_id)
    inspected = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image_id],
        capture_output=True, text=True, timeout=30, check=False,
    )
    if inspected.returncode or inspected.stdout.strip() != image_id:
        raise ValueError("frozen DEV image unavailable in Docker Engine")
    return {
        "schema": "e1c2-dev-constructor-pilot-freeze-v1", "run_id": RUN_ID,
        "instance_id": instance_id, "selection": "unique_public_constructor_parameter_request",
        "issue_quote": quote, "input_sha256": _sha(path),
        "base_admission_sha256": _sha(phase_paths[0]),
        "gold_admission_sha256": _sha(phase_paths[1]),
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "runner_module_sha256": _sha(Path(__file__)),
        "probe_module_sha256": _sha(ROOT / "evals/e1c_evaluation_2_probe.py"),
        "image_id": image_id, "estimated_call_reserve": reserve,
        "elastic_provider_ceiling": ceiling, "hard_provider_token_cap": HARD_PROVIDER_TOKEN_CAP,
        "model": "deepseek-flash", "thinking": "disabled", "sdk_retries": 0,
        "max_provider_calls": 1, "max_output_tokens_per_call": MAX_OUTPUT_TOKENS,
        "provider_calls": 0,
    }


async def run() -> dict:
    if not FREEZE.is_file() or json.loads(FREEZE.read_text(encoding="utf-8")) != preflight():
        raise ValueError("constructor pilot freeze missing or source/input changed")
    if LEDGER.exists() or (OUT / "state.json").exists():
        raise FileExistsError("constructor pilot already started; never auto-retry")
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek API credential unavailable")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    path, frozen, _ = _selected()
    if path.parent.name != freeze["instance_id"]:
        raise ValueError("selected public DEV task changed")
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
                    "provider_task_id": freeze["instance_id"],
                    "provider_total_token_ceiling": freeze["elastic_provider_ceiling"],
                    "provider_task_token_ceiling": freeze["elastic_provider_ceiling"],
                    "provider_max_calls_per_task": 1, "provider_max_output_tokens": MAX_OUTPUT_TOKENS,
                    "provider_prompt_reserve_multiplier": 1.4, "provider_disable_thinking": True,
                }}, role="e1c2_issue_only_constructor_probe_generator",
            )
        _save(OUT / "response.json", {
            "prompt_sha256": freeze["prompt_sha256"],
            "raw": content_text(response), "usage": usage_tokens(response),
        })
        state["status"] = "response_saved"
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
                          "elastic_provider_ceiling": value["elastic_provider_ceiling"],
                          "max_provider_calls": 1}, ensure_ascii=False))
    else:
        print(json.dumps(asyncio.run(run()), ensure_ascii=False))


if __name__ == "__main__":
    main()
