"""One-call-per-task DEV feedback pilot; never reads grader-only material."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
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
from evals.e1c_evaluation_2_dev_pilot import TASKS, _save, _sha
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import (
    execute_candidate,
    feedback_prompt,
    validate_candidate,
    verified_local_image,
)

RUN_ID = "e1c2-dev-feedback-pilot-v1"
ROOT_OUT = ROOT / ".codex/e1c/evaluation_2"
OUT = ROOT_OUT / RUN_ID
FREEZE = OUT / "freeze.json"
LEDGER = OUT / "provider_calls.jsonl"
REPLAY = ROOT_OUT / "e1c2-dev-probe-replay-v4/summary.json"
PREVIOUS = ROOT_OUT / "e1c2-dev-probe-pilot-v1"
MAX_PROVIDER_TOKENS = 9_000
MAX_OUTPUT_TOKENS = 1_200


def _prior(instance_id: str, summary: dict) -> tuple[str, str, str]:
    view = "behavior_expected"
    response_path = PREVIOUS / instance_id / view / "response.json"
    response = json.loads(response_path.read_text(encoding="utf-8"))
    source = json.loads(response["raw"])["source"]
    rows = [row for row in summary["rows"] if row["instance_id"] == instance_id and row["view"] == view]
    if len(rows) != 1 or rows[0].get("response_sha256") != _sha(response_path):
        raise ValueError("prior response does not match zero-call replay")
    if (
        rows[0].get("reasons") != ["no_prepatch_failure"]
        or rows[0].get("returncodes") != [0]
        or rows[0].get("probe_sha256") != hashlib.sha256(source.encode()).hexdigest()
    ):
        raise ValueError("prior DEV probe did not cleanly pass on unchanged base")
    return source, response["raw"], _sha(response_path)


def preflight() -> dict:
    summary = json.loads(REPLAY.read_text(encoding="utf-8"))
    if summary.get("schema") != "e1c2-dev-probe-replay-v4" or summary.get("provider_calls") != 0:
        raise ValueError("zero-call replay identity changed")
    rows = []
    for instance_id in TASKS:
        phase_paths = [ADMISSION / instance_id / f"{phase}.json" for phase in ("base", "gold")]
        phases = [json.loads(path.read_bytes()) for path in phase_paths]
        if any(phase.get("phase_pass") is not True or phase.get("provider_calls") != 0 for phase in phases):
            raise ValueError("feedback pilot requires official Base-Fail and Gold-Pass")
        input_path = ISSUE / instance_id / "frozen_input_v3.json"
        frozen = json.loads(input_path.read_text(encoding="utf-8"))
        previous_source, previous_raw, response_sha = _prior(instance_id, summary)
        previous = json.loads(previous_raw)
        validate_candidate(previous_source, previous["issue_quote"], frozen, workspace=SOURCE / instance_id)
        prompt = feedback_prompt(frozen, previous_source)
        image_id = verified_local_image(instance_id)
        inspected = subprocess.run(
            ["docker", "image", "inspect", "--format", "{{.Id}}", image_id],
            capture_output=True, text=True, timeout=30, check=False,
        )
        if inspected.returncode or inspected.stdout.strip() != image_id:
            raise ValueError("frozen DEV image is not available in Docker Engine")
        rows.append({
            "instance_id": instance_id,
            "input_sha256": _sha(input_path),
            "base_admission_sha256": _sha(phase_paths[0]),
            "gold_admission_sha256": _sha(phase_paths[1]),
            "prior_response_sha256": response_sha,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "image_id": image_id,
        })
    return {
        "schema": "e1c2-dev-feedback-pilot-freeze-v1",
        "run_id": RUN_ID, "tasks": rows,
        "prior_replay_sha256": _sha(REPLAY),
        "probe_module_sha256": _sha(ROOT / "evals/e1c_evaluation_2_probe.py"),
        "runner_module_sha256": _sha(Path(__file__)),
        "model": "deepseek-flash", "thinking": "disabled", "sdk_retries": 0,
        "max_provider_calls": 2, "max_provider_tokens": MAX_PROVIDER_TOKENS,
        "max_output_tokens_per_call": MAX_OUTPUT_TOKENS, "provider_calls": 0,
    }


async def run() -> dict:
    if not FREEZE.is_file() or json.loads(FREEZE.read_text(encoding="utf-8")) != preflight():
        raise ValueError("feedback pilot freeze missing or source/input changed")
    if LEDGER.exists() or (OUT / "state.json").exists():
        raise FileExistsError("feedback pilot already started; never auto-retry provider calls")
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek API credential unavailable")
    state = {"run_id": RUN_ID, "status": "running", "rows": [], "trusted_reproducer_count": 0}
    _save(OUT / "state.json", state)
    summary = json.loads(REPLAY.read_text(encoding="utf-8"))
    async with httpx.AsyncClient(trust_env=False, timeout=90) as client:
        model = ChatOpenAI(
            model="deepseek-flash", temperature=0, streaming=False,
            openai_api_base="https://api.deepseek.com", openai_api_key=settings.DEEPSEEK_API_KEY,
            max_retries=0, http_async_client=client,
        )
        try:
            for row in json.loads(FREEZE.read_text(encoding="utf-8"))["tasks"]:
                instance_id = row["instance_id"]
                frozen = json.loads((ISSUE / instance_id / "frozen_input_v3.json").read_text(encoding="utf-8"))
                previous_source, _, _ = _prior(instance_id, summary)
                prompt = feedback_prompt(frozen, previous_source)
                if hashlib.sha256(prompt.encode()).hexdigest() != row["prompt_sha256"]:
                    raise ValueError("feedback prompt changed after freeze")
                response = await budgeted_ainvoke(
                    model, [HumanMessage(content=prompt)],
                    {"configurable": {
                        "provider_ledger_path": str(LEDGER), "provider_run_id": RUN_ID,
                        "provider_task_id": instance_id, "provider_total_token_ceiling": MAX_PROVIDER_TOKENS,
                        "provider_task_token_ceiling": 4_500, "provider_max_calls_per_task": 1,
                        "provider_max_output_tokens": MAX_OUTPUT_TOKENS,
                        "provider_prompt_reserve_multiplier": 1.4,
                        "provider_disable_thinking": True,
                    }},
                    role="e1c2_issue_only_feedback_probe_generator",
                )
                raw = content_text(response)
                call_dir = OUT / instance_id
                _save(call_dir / "response.json", {"prompt_sha256": row["prompt_sha256"],
                                                     "raw": raw, "usage": usage_tokens(response)})
                result = {"instance_id": instance_id, "status": "response_saved"}
                try:
                    value = json.loads(raw)
                    if isinstance(value, dict) and set(value) == {"abstain_reason"}:
                        result.update({"status": "abstained", "reason": str(value["abstain_reason"])[:300]})
                    else:
                        if not isinstance(value, dict) or set(value) != {"source", "issue_quote"}:
                            raise ValueError("response must contain source/issue_quote or abstain_reason")
                        candidate = validate_candidate(
                            value["source"], value["issue_quote"], frozen, workspace=SOURCE / instance_id
                        )
                        _save(call_dir / "candidate.json", candidate)
                        execution = execute_candidate(
                            candidate, row["image_id"], frozen["base_commit"], call_dir / "execution"
                        )
                        _save(call_dir / "execution.json", execution)
                        result.update({"status": "executed", "repeatable_failure_candidate":
                                       execution["repeatable_failure_candidate"],
                                       "reasons": [item["reason"] for item in execution["runs"]]})
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
                raise ValueError("existing feedback freeze differs; no silent overwrite")
        else:
            _save(FREEZE, value)
        print(json.dumps({"ready": True, "freeze": str(FREEZE), "tasks": TASKS,
                          "max_provider_calls": 2, "max_provider_tokens": MAX_PROVIDER_TOKENS}, ensure_ascii=False))
    else:
        value = asyncio.run(run())
        print(json.dumps({"status": value["status"], "rows": len(value["rows"]),
                          "trusted_reproducer_count": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
