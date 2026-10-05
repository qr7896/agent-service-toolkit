"""Prospective DEV source-contract controller with a pre-grader fallback."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import math
import shutil

import httpx

from agents.model_budget import _prompt_text, budgeted_ainvoke
from agents.model_router import estimate_tokens
from core.settings import settings
from evals import e1c_evaluation_2_contract_ab_dev_v2 as prompts
from evals import e1c_evaluation_2_production_coverage as coverage
from evals.e1c_evaluation_2_contract_method import parse_response
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_pregrader_policy import failure_signal
from evals.e1c_evaluation_2_probe import execute_candidate, validate_candidate, verified_local_image
from evals.e1c_evaluation_2_raw_json import RawJsonFlash, response_record
from evals.e1c_evaluation_2_source_contract import build_source_pair, optional_import

OUT = ROOT / ".codex/e1c/evaluation_2/hybrid-dev-v1"
PROTOCOL = ROOT / "docs/research/E1C2_HYBRID_DEV_PROTOCOL_2026-10-05.md"
IDENTITY = prompts.original.IDENTITY
FIXED_DENOMINATOR = 12
TASK_CAP, BATCH_CAP, OUTPUT_CAP = 20_000, 100_000, 3000


def inputs():
    return [(row["instance_id"], json.loads(path.read_bytes()), path, coverage.SOURCE / row["instance_id"],
             verified_local_image(row["instance_id"])) for row in coverage.prepare()["rows"]
            for path in [coverage.OUT / "inputs" / f"{row['instance_id']}.json"]]


def model_messages(frozen, role):
    # Model instructions/views are the frozen v2 pair, with no grader feedback.
    return prompts.messages(frozen, role)


def preflight():
    rows = []
    for iid, frozen, path, workspace, image in inputs():
        reserves = {role: math.ceil(estimate_tokens(_prompt_text(model_messages(frozen, role))) * 1.4) + OUTPUT_CAP
                    for role in ("B", "A")}
        if any(value > TASK_CAP for value in reserves.values()):
            raise ValueError("a candidate reserve exceeds its joint task cap")
        rows.append({"instance_id": iid, "image_id": image, "input_sha256": _sha(path), "reserves": reserves,
                     "environment": optional_import(frozen, workspace)})
    primary = sum(row["reserves"]["B"] for row in rows)
    if primary > BATCH_CAP:
        raise ValueError("primary prompts do not fit the batch cap")
    return {"schema": "e1c2-source-contract-hybrid-freeze-v1", "fixed_denominator": FIXED_DENOMINATOR,
            "tasks": rows, "identity_sha256": _sha(IDENTITY), "model": "deepseek-flash", "thinking": "disabled",
            "temperature": 0, "max_provider_calls": 2 * len(rows), "max_calls_per_task": 2,
            "task_token_cap": TASK_CAP, "batch_token_cap": BATCH_CAP, "max_output_tokens": OUTPUT_CAP,
            "primary_reserve": primary, "fallback_budget": "online_actual_usage_plus_reserve_no_budget_borrowing",
            "protocol_sha256": _sha(PROTOCOL), "modules": {name: _sha(ROOT / name) for name in (
                "evals/e1c_evaluation_2_hybrid_dev.py", "evals/e1c_evaluation_2_source_contract.py",
                "evals/e1c_evaluation_2_raw_json.py", "evals/e1c_evaluation_2_contract_ab_dev_v2.py",
                "evals/e1c_evaluation_2_contract_ab_dev.py", "evals/e1c_evaluation_2_contract_method.py",
                "evals/e1c_evaluation_2_production_coverage.py", "evals/e1c_evaluation_2_pregrader_policy.py")}, "provider_calls": 0}


def freeze():
    value = preflight()
    path = OUT / "freeze.json"
    if path.exists():
        if json.loads(path.read_bytes()) != value:
            raise ValueError("hybrid freeze changed")
    else:
        _save(path, value)
    return value


def execute_role(role, payload, frozen, workspace, image, root, environment):
    if role == "B":
        control, candidate, frontier = build_source_pair(payload, frozen, workspace)
        _save(root / "frontier.json", frontier)
        _save(root / "control_candidate.json", control)
        controls = [execute_candidate(control, image, frozen["base_commit"], root / f"control-{n}",
                    missing_optional_import=environment["missing_optional_import"]) for n in (1, 2)]
        _save(root / "control_execution.json", {"runs": controls})
        if not all(item["runs"] and all(row["returncode"] == 0 and not row["timed_out"] for row in item["runs"]) for item in controls):
            return {"status": "fixture_or_positive_control_failed", "control_pass": False}
    else:
        candidate = validate_candidate(payload["source"], frozen["issue"].splitlines()[0], frozen, workspace=workspace)
    _save(root / "candidate.json", candidate)
    execution = execute_candidate(candidate, image, frozen["base_commit"], root / "execution",
                missing_optional_import=environment["missing_optional_import"], repeat_nonsetup_failure=True)
    _save(root / "execution.json", execution)
    return {"status": "executed", "control_pass": role == "B",
            "repeatable_failure_candidate": execution["repeatable_failure_candidate"],
            "repeatable_nonsetup_failure": execution["repeatable_nonsetup_failure"]}


async def run():
    frozen_run = json.loads((OUT / "freeze.json").read_bytes())
    if frozen_run != preflight():
        raise ValueError("hybrid inputs/method changed")
    ledger, state_path = OUT / "provider_calls.jsonl", OUT / "state.json"
    if ledger.exists() or state_path.exists():
        raise FileExistsError("hybrid run started; no automatic retry")
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek credential unavailable")
    state = {"status": "running", "fixed_denominator": FIXED_DENOMINATOR, "rows": [], "trusted_reproducer_count": 0}
    _save(state_path, state)
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=120) as client:
            model = RawJsonFlash(model="deepseek-flash", temperature=0, streaming=False, max_retries=0,
                                 openai_api_base="https://api.deepseek.com", openai_api_key=settings.DEEPSEEK_API_KEY,
                                 http_async_client=client)
            for row, (iid, frozen, _, workspace, image) in zip(frozen_run["tasks"], inputs(), strict=True):
                task_dir = OUT / iid
                final = {"instance_id": iid, "status": "no_repeatable_witness", "roles": [], "selected_role": None}
                for role in ("B", "A"):
                    bound = model.bind(response_format={"type": "json_object"}) if role == "B" else model
                    response = await budgeted_ainvoke(bound, model_messages(frozen, role), {"configurable": {
                        "provider_ledger_path": str(ledger), "provider_run_id": OUT.name, "provider_task_id": iid,
                        "provider_total_token_ceiling": BATCH_CAP, "provider_task_token_ceiling": TASK_CAP,
                        "provider_max_calls_per_task": 2, "provider_max_output_tokens": OUTPUT_CAP,
                        "provider_prompt_reserve_multiplier": 1.4, "provider_disable_thinking": True,
                    }}, role=f"e1c2_hybrid_{role}")
                    record = response_record(response)
                    root = task_dir / role
                    _save(root / "response.json", record)
                    try:
                        if record["response_status"] != "received":
                            result = {"status": "response_" + record["response_status"]}
                        else:
                            parsed = parse_response(record["raw"], role)
                            result = {"status": "abstained", "reason": parsed["reason"]} if parsed["status"] == "abstained" else (
                                execute_role(role, parsed["payload"], frozen, workspace, image, root, row["environment"]))
                    except (ValueError, SyntaxError, TypeError) as exc:
                        result = {"status": "candidate_rejected", "reason": f"{type(exc).__name__}: {exc}"}
                    final["roles"].append({"role": role, **result})
                    if failure_signal(result):
                        candidate = json.loads((root / "candidate.json").read_bytes())
                        execution = json.loads((root / "execution.json").read_bytes())
                        _save(task_dir / "candidate.json", candidate)
                        _save(task_dir / "execution.json", execution)
                        folder = task_dir / "execution"
                        folder.mkdir(exist_ok=True)
                        name = candidate["probe_sha256"] + ".py"
                        shutil.copy2(root / "execution" / name, folder / name)
                        if execution.get("missing_optional_import"):
                            shutil.copytree(root / "execution" / "optional_missing", folder / "optional_missing")
                        if _sha(folder / name) != candidate["probe_sha256"]:
                            raise ValueError("selected probe changed during artifact copy")
                        final.update({"status": "executed", "selected_role": role,
                                      "repeatable_failure_candidate": result["repeatable_failure_candidate"],
                                      "repeatable_nonsetup_failure": result["repeatable_nonsetup_failure"]})
                        break
                state["rows"].append(final)
                state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(json.dumps(final, ensure_ascii=False), flush=True)
    except Exception as exc:
        state.update({"status": "interrupted_no_auto_retry", "error": f"{type(exc).__name__}: {exc}"})
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise
    state["status"] = "completed"
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"attempted": len(state["rows"]), "status": state["status"], "trusted_reproducer_count": 0}


def grade():
    from evals import e1c_evaluation_2_unified_dev_v2_gold as gold

    importlib.import_module("evals.e1c_evaluation_2_unified_dev_v4")
    gold.base.OUT, gold.base.FREEZE, gold.base.preflight = OUT, OUT / "freeze.json", preflight
    gold.GRADER, gold.OUT = prompts.original.ADMISSION, OUT / "gold-discrimination"
    return gold.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "gold"))
    args = parser.parse_args()
    if args.command == "preflight":
        value = freeze()
        print(json.dumps({key: value[key] for key in ("model", "max_provider_calls", "primary_reserve", "batch_token_cap")}))
    else:
        print(json.dumps(asyncio.run(run()) if args.command == "run" else grade()))
