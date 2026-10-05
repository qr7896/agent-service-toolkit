"""Matched old-DEV comparison of v4-style probes and contracts with positive controls."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib
import json
import math
import subprocess
from pathlib import Path

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agents.model_budget import _prompt_text, budgeted_ainvoke
from agents.model_router import estimate_tokens
from core.settings import settings
from evals.e1b_editor_adapter import content_text, usage_tokens
from evals.e1c_evaluation_2 import IDENTITY, ROOT
from evals.e1c_evaluation_2_admission import OUT as ADMISSION
from evals.e1c_evaluation_2_contract_method import build_pair, coverage_input, parse_response
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import (
    execute_candidate,
    input_json,
    issue_missing_optional_import,
    validate_candidate,
    verified_local_image,
)
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

OUT = ROOT / ".codex/e1c/evaluation_2/contract-ab-dev-v1"
PROTOCOL = ROOT / "docs/research/E1C2_CONTRACT_AB_DEV_PROTOCOL_2026-10-05.md"
MODEL = "deepseek-flash"
MAX_OUTPUT_TOKENS = 3000
TASK_TOKEN_CAP = 12_000
BATCH_TOKEN_CAP = 90_000


def prepare() -> list[tuple[str, dict, Path]]:
    rows = []
    for task in json.loads(IDENTITY.read_bytes())["tasks"]:
        iid = task["instance_id"]
        phases = [ADMISSION / iid / f"{phase}.json" for phase in ("base", "gold")]
        if not all(json.loads(path.read_bytes()).get("phase_pass") is True for path in phases):
            continue
        old_path = ISSUE / iid / "frozen_input_v4.json"
        old = json.loads(old_path.read_bytes())
        head = subprocess.check_output(["git", "-C", str(SOURCE / iid), "rev-parse", "HEAD"], text=True, timeout=30).strip()
        status = subprocess.check_output(["git", "-C", str(SOURCE / iid), "status", "--porcelain", "--untracked-files=all"],
                                         text=True, timeout=90).strip()
        if head != old["base_commit"] or status:
            raise ValueError("old DEV source is not clean at its exact base")
        frozen = coverage_input(old, SOURCE / iid)
        path = OUT / "inputs" / f"{iid}.json"
        if path.exists():
            if json.loads(path.read_bytes()) != frozen:
                raise ValueError("prepared common DEV input changed")
        else:
            _save(path, frozen)
        rows.append((iid, frozen, path))
    if len(rows) != 9:
        raise ValueError("expected all nine admitted old DEV tasks; no outcome selection")
    return rows


def messages(frozen: dict, arm: str) -> list:
    if arm == "A":
        from evals.e1c_evaluation_2_unified_dev_v4 import prompt

        return [HumanMessage(content=prompt(frozen))]
    instruction = (
        "Generate one issue-grounded executable reproducer using only the public issue and production windows. "
        "Return JSON, never copy the input issue/windows. Return exactly {\"abstain_reason\":\"reason\"} if the "
        "behavior or a valid fixture cannot be established. Otherwise return exactly seven string fields: "
        "issue_quote, expected_quote, oracle, setup_source, control_action, target_action, assertion. "
        "Both quote fields must be verbatim spans from this issue. oracle is call_completes or value_relation. "
        "setup_source contains imports, classes and fixtures only, no assertions or exception catches. "
        "control_action must call the same real public API on a known-valid baseline case that should complete "
        "on unchanged code; never replace it with a dummy call. target_action exercises the reported failing "
        "case preserving input types and preconditions. Do not fabricate failures or invalid objects. "
        "For call_completes, assertion must be the empty string; the controller inserts a completion check. "
        "For value_relation, assertion is exactly one comparison assert of the issue-stated expectation; "
        "do not add an unstated value or property. No try/except, forced raises, fake warnings, network, files, "
        "subprocess, installation, test inspection, task IDs or changes to production code. "
        "Keep source compact. Constructed fixtures must provide every member required by shown production signatures."
    )
    context = input_json({"issue": frozen["issue"], "windows": frozen["windows"]})
    audit_repair_visible_payload({"instruction": instruction, "context": context})
    return [SystemMessage(content=instruction), HumanMessage(content=context)]


def preflight(arm: str) -> dict:
    tasks = []
    for iid, frozen, path in prepare():
        msg = messages(frozen, arm)
        text = _prompt_text(msg)
        reserve = math.ceil(estimate_tokens(text) * 1.4) + MAX_OUTPUT_TOKENS
        if reserve > TASK_TOKEN_CAP:
            raise ValueError(f"task reserve exceeds matched hard cap: {iid}")
        image = verified_local_image(iid)
        actual = subprocess.check_output(["docker", "image", "inspect", image, "--format", "{{.Id}}"], text=True, timeout=30).strip()
        if actual != image:
            raise ValueError("old DEV image identity changed")
        tasks.append({"instance_id": iid, "input_sha256": _sha(path), "image_id": image,
                      "prompt_sha256": hashlib.sha256(text.encode()).hexdigest(), "estimated_reserve": reserve,
                      "missing_optional_import": issue_missing_optional_import(frozen)})
    total = sum(row["estimated_reserve"] for row in tasks)
    if total > BATCH_TOKEN_CAP:
        raise ValueError("matched arm reserve exceeds batch cap")
    modules = ("evals/e1c_evaluation_2_contract_ab_dev.py", "evals/e1c_evaluation_2_contract_method.py",
               "evals/e1c_evaluation_2_unified_dev_v4.py", "evals/e1c_evaluation_2_probe.py",
               "evals/e1c_blind_evidence.py", "evals/e1c_evaluation_2_unified_dev_v2_gold.py", "src/agents/model_budget.py")
    return {"schema": "e1c2-contract-ab-dev-arm-freeze-v1", "arm": arm,
            "run_id": f"e1c2-contract-ab-dev-v1-{arm.lower()}", "selection": "all_nine_admitted_old_DEV_no_outcome_selection",
            "fixed_denominator": 12, "tasks": tasks, "model": MODEL, "thinking": "disabled", "temperature": 0,
            "sdk_retries": 0, "max_provider_calls": 9, "max_output_tokens_per_call": MAX_OUTPUT_TOKENS,
            "per_task_token_cap": TASK_TOKEN_CAP, "batch_token_cap": BATCH_TOKEN_CAP,
            "elastic_token_ceiling": BATCH_TOKEN_CAP, "total_reserve": total, "identity_sha256": _sha(IDENTITY),
            "protocol_sha256": _sha(PROTOCOL), "modules": {name: _sha(ROOT / name) for name in modules},
            "response_format": {"type": "json_object"} if arm == "B" else None, "provider_calls": 0}


def freeze(arm: str) -> dict:
    value = preflight(arm)
    path = OUT / arm / "freeze.json"
    if path.exists():
        if json.loads(path.read_bytes()) != value:
            raise ValueError("arm freeze changed")
    else:
        _save(path, value)
    return value


async def run(arm: str) -> dict:
    destination = OUT / arm
    frozen_run = json.loads((destination / "freeze.json").read_bytes())
    if frozen_run != preflight(arm):
        raise ValueError("DEV arm freeze changed")
    ledger = destination / "provider_calls.jsonl"
    state_path = destination / "state.json"
    if ledger.exists() or state_path.exists():
        raise FileExistsError("DEV arm already started; no automatic provider retry")
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek credential unavailable")
    state = {"run_id": frozen_run["run_id"], "arm": arm, "status": "running", "rows": [], "trusted_reproducer_count": 0}
    _save(state_path, state)
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=120) as client:
            options = {"model_kwargs": {"response_format": {"type": "json_object"}}} if arm == "B" else {}
            model = ChatOpenAI(model=MODEL, temperature=0, streaming=False, openai_api_base="https://api.deepseek.com",
                               openai_api_key=settings.DEEPSEEK_API_KEY, max_retries=0, http_async_client=client, **options)
            for row, (iid, frozen, _) in zip(frozen_run["tasks"], prepare(), strict=True):
                task_dir = destination / iid
                response = await budgeted_ainvoke(model, messages(frozen, arm), {"configurable": {
                    "provider_ledger_path": str(ledger), "provider_run_id": frozen_run["run_id"], "provider_task_id": iid,
                    "provider_total_token_ceiling": BATCH_TOKEN_CAP, "provider_task_token_ceiling": TASK_TOKEN_CAP,
                    "provider_max_calls_per_task": 1, "provider_max_output_tokens": MAX_OUTPUT_TOKENS,
                    "provider_prompt_reserve_multiplier": 1.4, "provider_disable_thinking": True,
                }}, role="e1c2_contract_ab_dev")
                raw = content_text(response)
                metadata = response.response_metadata or {}
                _save(task_dir / "response.json", {"raw": raw, "usage": usage_tokens(response),
                      "prompt_sha256": row["prompt_sha256"], "finish_reason": metadata.get("finish_reason"),
                      "provider_model": metadata.get("model_name")})
                status = {"instance_id": iid, "status": "response_saved"}
                try:
                    parsed = parse_response(raw, arm)
                    if parsed["status"] == "abstained":
                        status.update({"status": "abstained", "reason": parsed["reason"]})
                    else:
                        if arm == "B":
                            control, candidate = build_pair(parsed["payload"], frozen, SOURCE / iid)
                            _save(task_dir / "contract.json", parsed["payload"])
                            _save(task_dir / "control_candidate.json", control)
                            controls = [execute_candidate(control, row["image_id"], frozen["base_commit"],
                                        task_dir / f"control-{n}", missing_optional_import=row["missing_optional_import"])
                                        for n in (1, 2)]
                            _save(task_dir / "control_execution.json", {"runs": controls})
                            control_pass = all(item["runs"] and all(r["returncode"] == 0 and not r["timed_out"]
                                               for r in item["runs"]) for item in controls)
                            status["control_pass"] = control_pass
                        else:
                            candidate = validate_candidate(parsed["payload"]["source"], frozen["issue"].splitlines()[0].strip(),
                                                           frozen, workspace=SOURCE / iid)
                            control_pass = True
                        _save(task_dir / "candidate.json", candidate)
                        if not control_pass:
                            status["status"] = "fixture_or_positive_control_failed"
                        else:
                            execution = execute_candidate(candidate, row["image_id"], frozen["base_commit"],
                                        task_dir / "execution", missing_optional_import=row["missing_optional_import"],
                                        repeat_nonsetup_failure=True)
                            _save(task_dir / "execution.json", execution)
                            status.update({"status": "executed", "repeatable_failure_candidate": execution["repeatable_failure_candidate"],
                                           "repeatable_nonsetup_failure": execution["repeatable_nonsetup_failure"],
                                           "reasons": [item["reason"] for item in execution["runs"]]})
                except (ValueError, SyntaxError, TypeError) as exc:
                    status.update({"status": "candidate_rejected", "reason": f"{type(exc).__name__}: {exc}"})
                state["rows"].append(status)
                state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(json.dumps(status, ensure_ascii=False), flush=True)
    except Exception as exc:
        state.update({"status": "interrupted_no_auto_retry", "error": f"{type(exc).__name__}: {exc}"})
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise
    state["status"] = "completed"
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"arm": arm, "status": state["status"], "attempted": len(state["rows"]), "trusted_reproducer_count": 0}


def grade(arm: str) -> dict:
    from evals import e1c_evaluation_2_unified_dev_v2_gold as gold

    if arm == "A":
        # Load the historical prompt override before binding the new grader namespace.
        importlib.import_module("evals.e1c_evaluation_2_unified_dev_v4")
    gold.base.OUT = OUT / arm
    gold.base.FREEZE = OUT / arm / "freeze.json"
    gold.base.preflight = lambda: preflight(arm)
    gold.GRADER, gold.OUT = ADMISSION, OUT / arm / "gold-discrimination"
    return gold.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "preflight", "run", "gold"))
    parser.add_argument("--arm", choices=("A", "B"), default="B")
    args = parser.parse_args()
    if args.command == "prepare":
        result = {"prepared": len(prepare()), "provider_calls": 0}
    elif args.command == "preflight":
        value = freeze(args.arm)
        result = {key: value[key] for key in ("arm", "model", "max_provider_calls", "total_reserve", "batch_token_cap")}
    elif args.command == "run":
        result = asyncio.run(run(args.arm))
    else:
        result = grade(args.arm)
    print(json.dumps(result, ensure_ascii=False))
