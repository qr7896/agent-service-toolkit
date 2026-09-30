"""Frozen, two-repository DEV probe pilot; never opens grader-only files."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

import httpx
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from agents.model_budget import budgeted_ainvoke
from core.settings import settings
from evals.e1b_editor_adapter import content_text, usage_tokens
from evals.e1c_blind_boundary import BlindBoundaryViolation
from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_admission import OUT as ADMISSION
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_probe import (
    execute_candidate,
    generation_views,
    validate_candidate,
    verified_local_image,
)
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

RUN_ID = "e1c2-dev-probe-pilot-v1"
TASKS = ("marshmallow-code__marshmallow-1252", "pytest-dev__pytest-6680")
OUT = ROOT / ".codex/e1c/evaluation_2" / RUN_ID
FREEZE = OUT / "freeze.json"
LEDGER = OUT / "provider_calls.jsonl"
MAX_PROVIDER_TOKENS = 18_000
MAX_OUTPUT_TOKENS = 900


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def preflight() -> dict:
    rows = []
    for instance_id in TASKS:
        phase_files = [ADMISSION / instance_id / f"{phase}.json" for phase in ("base", "gold")]
        phases = [json.loads(path.read_text(encoding="utf-8")) for path in phase_files]
        if any(row.get("phase_pass") is not True or row.get("provider_calls") != 0 for row in phases):
            raise ValueError("two-repository pilot requires verified Base-Fail and Gold-Pass")
        input_path = ISSUE / instance_id / "frozen_input_v2.json"
        frozen = json.loads(input_path.read_text(encoding="utf-8"))
        if frozen.get("schema") != "e1c-evaluation-2-probe-input-v2":
            raise ValueError("issue-only input is not frozen v2")
        views = generation_views(frozen)
        if len(views) != 2:
            raise ValueError("each pilot task requires two fixed issue-only views")
        for view in views:
            audit_repair_visible_payload(view)
        rows.append({
            "instance_id": instance_id, "input_sha256": _sha(input_path),
            "base_admission_sha256": _sha(phase_files[0]), "gold_admission_sha256": _sha(phase_files[1]),
            "image_id": verified_local_image(instance_id),
            "view_prompt_sha256": {view["view"]: hashlib.sha256(view["prompt"].encode()).hexdigest() for view in views},
        })
    return {
        "schema": "e1c-evaluation-2-dev-probe-pilot-freeze-v1",
        "run_id": RUN_ID, "tasks": rows, "task_count": 2, "view_count": 4,
        "model": "deepseek-flash", "thinking": "disabled", "sdk_retries": 0,
        "max_provider_calls": 4, "max_provider_tokens": MAX_PROVIDER_TOKENS,
        "max_output_tokens_per_call": MAX_OUTPUT_TOKENS,
        "probe_module_sha256": _sha(ROOT / "evals/e1c_evaluation_2_probe.py"),
        "runner_module_sha256": _sha(Path(__file__)),
        "provider_calls": 0,
    }


async def run() -> dict:
    if not FREEZE.is_file() or json.loads(FREEZE.read_text(encoding="utf-8")) != preflight():
        raise ValueError("pilot freeze missing or code/input/admission changed")
    if LEDGER.exists() or (OUT / "state.json").exists():
        raise FileExistsError("pilot already started; never auto-retry provider calls")
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek API credential unavailable")
    state = {"run_id": RUN_ID, "status": "running", "rows": [], "trusted_reproducer_count": 0}
    _save(OUT / "state.json", state)
    async with httpx.AsyncClient(trust_env=False, timeout=90) as client:
        model = ChatOpenAI(
            model="deepseek-flash", temperature=0, streaming=False,
            openai_api_base="https://api.deepseek.com", openai_api_key=settings.DEEPSEEK_API_KEY,
            max_retries=0, http_async_client=client,
        )
        try:
            for row in json.loads(FREEZE.read_text(encoding="utf-8"))["tasks"]:
                instance_id = row["instance_id"]
                frozen = json.loads((ISSUE / instance_id / "frozen_input_v2.json").read_text(encoding="utf-8"))
                for view in generation_views(frozen):
                    key = f"{instance_id}:{view['view']}"
                    response = await budgeted_ainvoke(
                        model, [HumanMessage(content=view["prompt"])],
                        {"configurable": {
                            "provider_ledger_path": str(LEDGER), "provider_run_id": RUN_ID,
                            "provider_task_id": key, "provider_total_token_ceiling": MAX_PROVIDER_TOKENS,
                            "provider_task_token_ceiling": 6_000, "provider_max_calls_per_task": 1,
                            "provider_max_output_tokens": MAX_OUTPUT_TOKENS,
                            "provider_prompt_reserve_multiplier": 1.4,
                            "provider_disable_thinking": True,
                        }},
                        role="e1c2_issue_only_probe_generator",
                    )
                    raw = content_text(response)
                    call_dir = OUT / instance_id / view["view"]
                    _save(call_dir / "response.json", {
                        "prompt_sha256": row["view_prompt_sha256"][view["view"]],
                        "raw": raw, "usage": usage_tokens(response),
                    })
                    result = {"instance_id": instance_id, "view": view["view"], "status": "response_saved"}
                    try:
                        value = json.loads(raw)
                        if not isinstance(value, dict) or set(value) != {"source", "issue_quote"}:
                            raise ValueError("response must contain only source and issue_quote")
                        candidate = validate_candidate(value["source"], value["issue_quote"], frozen)
                        _save(call_dir / "candidate.json", candidate)
                        execution = execute_candidate(
                            candidate, row["image_id"], frozen["base_commit"], call_dir / "execution"
                        )
                        _save(call_dir / "execution.json", execution)
                        result.update({
                            "status": "executed", "repeatable_failure_candidate": execution["repeatable_failure_candidate"],
                            "reasons": [item["reason"] for item in execution["runs"]],
                        })
                    except (BlindBoundaryViolation, ValueError, SyntaxError) as exc:
                        result.update({"status": "candidate_rejected", "reason": f"{type(exc).__name__}: {exc}"})
                    state["rows"].append(result)
                    (OUT / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    print(json.dumps(result, ensure_ascii=False), flush=True)
        except Exception as exc:
            state.update({"status": "interrupted_no_auto_retry", "error": f"{type(exc).__name__}: {exc}"})
            (OUT / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            raise
    state["status"] = "completed"
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
                raise ValueError("existing pilot freeze differs from current code/input/admission")
        else:
            _save(FREEZE, value)
        print(json.dumps({"ready": True, "freeze": str(FREEZE), "tasks": TASKS,
                          "max_provider_calls": 4, "max_provider_tokens": MAX_PROVIDER_TOKENS}, ensure_ascii=False))
    else:
        value = asyncio.run(run())
        print(json.dumps({"status": value["status"], "rows": len(value["rows"]),
                          "trusted_reproducer_count": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
