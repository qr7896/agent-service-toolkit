"""One frozen issue-only reproducer method across every admitted E1-C DEV12 task."""

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
from evals.e1c_evaluation_2 import IDENTITY, ROOT
from evals.e1c_evaluation_2_admission import OUT as ADMISSION
from evals.e1c_evaluation_2_constructor_rule import _REQUEST, source_from_public_issue
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_feedback_v2 import _source
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

RUN_ID = "e1c2-unified-dev-v1"
OUT = ROOT / ".codex/e1c/evaluation_2" / RUN_ID
FREEZE = OUT / "freeze.json"
LEDGER = OUT / "provider_calls.jsonl"
MODEL = "deepseek-v4-pro"
MAX_OUTPUT_TOKENS = 2400
TASK_TOKEN_CAP = 12_000
BATCH_TOKEN_CAP = 80_000


def route(frozen: dict) -> tuple[str, str | None]:
    """The same public-text route applies to DEV and later independent tasks."""
    matches = list(_REQUEST.finditer(frozen["issue"]))
    if len(matches) == 1:
        quote = matches[0].group(0)
        try:
            return "deterministic_boolean_constructor", source_from_public_issue(frozen["issue"], quote)
        except ValueError:
            pass
    return "model_public_issue", None


def quote(frozen: dict, method: str) -> str:
    if method == "deterministic_boolean_constructor":
        return _REQUEST.search(frozen["issue"]).group(0)
    return frozen["issue"].splitlines()[0].strip()


def prompt(frozen: dict) -> str:
    context = input_json({"issue": frozen["issue"], "windows": frozen["windows"]})
    if len(context) > 24_000:
        raise ValueError("issue-only context too large")
    value = (
        "Using only this public issue and exact-base production-source windows, write one standalone Python "
        "script that reproduces the issue's stated behavior. Execute the production public API directly and "
        "include an explicit assert on its actual result, warning, or exception. Preserve the issue's input "
        "type and stated preconditions; do not invent missing data, manufacture the expected warning/error, "
        "or simulate the production function. If the public report lacks enough information for a sound "
        "reproducer, abstain. Do not inspect tests, hidden patches, grader artifacts or task IDs, change "
        "production files, install packages, invoke network, or use subprocess/I/O helpers. "
        "Return only JSON: {\"source\": \"complete executable Python source\"} or "
        "{\"abstain_reason\": \"brief public-evidence reason\"}.\n" + context
    )
    audit_repair_visible_payload(value)
    return value


def _admitted_inputs() -> list[tuple[str, dict, Path]]:
    rows = []
    for task in json.loads(IDENTITY.read_bytes())["tasks"]:
        instance_id = task["instance_id"]
        admissions = [ADMISSION / instance_id / f"{phase}.json" for phase in ("base", "gold")]
        if not all(json.loads(path.read_text(encoding="utf-8")).get("phase_pass") is True for path in admissions):
            continue
        path = ISSUE / instance_id / "frozen_input_v4.json"
        frozen = json.loads(path.read_text(encoding="utf-8"))
        if frozen.get("schema") != "e1c-evaluation-2-probe-input-v4" or frozen.get("status") != "ready_for_generation":
            raise ValueError(f"admitted DEV input unavailable: {instance_id}")
        rows.append((instance_id, frozen, path))
    if len(rows) != 9:
        raise ValueError(f"expected 9/12 admitted DEV inputs, found {len(rows)}")
    return rows


def preflight() -> dict:
    rows = []
    for instance_id, frozen, path in _admitted_inputs():
        method, source = route(frozen)
        issue_quote = quote(frozen, method)
        if source is not None:
            validate_candidate(source, issue_quote, frozen, workspace=SOURCE / instance_id)
        model_prompt = prompt(frozen) if source is None else None
        reserve = (
            math.ceil(estimate_tokens(_prompt_text([HumanMessage(content=model_prompt)])) * 1.4)
            + MAX_OUTPUT_TOKENS if model_prompt is not None else 0
        )
        if reserve > TASK_TOKEN_CAP:
            raise ValueError(f"DEV prompt reserve exceeds task cap: {instance_id}")
        rows.append({
            "instance_id": instance_id,
            "method": method,
            "input_sha256": _sha(path),
            "prompt_sha256": hashlib.sha256(model_prompt.encode()).hexdigest() if model_prompt else None,
            "source_sha256": hashlib.sha256(source.encode()).hexdigest() if source else None,
            "image_id": verified_local_image(instance_id),
            "missing_optional_import": issue_missing_optional_import(frozen),
            "estimated_reserve": reserve,
        })
    total = sum(row["estimated_reserve"] for row in rows)
    if total > BATCH_TOKEN_CAP:
        raise ValueError("DEV total reserve exceeds hard cap")
    return {
        "schema": "e1c2-unified-dev-v1-freeze", "run_id": RUN_ID,
        "selection": "all_nine_frozen_DEV12_officially_admitted_no_outcome_selection",
        "tasks": rows, "model": MODEL, "thinking": "disabled", "sdk_retries": 0,
        "max_provider_calls": sum(row["method"] == "model_public_issue" for row in rows),
        "max_output_tokens_per_call": MAX_OUTPUT_TOKENS,
        "per_task_token_cap": TASK_TOKEN_CAP, "batch_token_cap": BATCH_TOKEN_CAP,
        "total_reserve": total,
        "elastic_token_ceiling": min(BATCH_TOKEN_CAP, math.ceil(total * 1.25)),
        "identity_sha256": _sha(IDENTITY), "runner_sha256": _sha(Path(__file__)),
        "probe_sha256": _sha(ROOT / "evals/e1c_evaluation_2_probe.py"),
        "constructor_rule_sha256": _sha(ROOT / "evals/e1c_evaluation_2_constructor_rule.py"),
        "public_input_sha256": _sha(ROOT / "evals/e1c_evaluation_2_issue_input_v4.py"),
        "provider_calls": 0,
    }


async def run() -> dict:
    if not FREEZE.is_file() or json.loads(FREEZE.read_text(encoding="utf-8")) != preflight():
        raise ValueError("unified DEV freeze missing or changed")
    if LEDGER.exists() or (OUT / "state.json").exists():
        raise FileExistsError("unified DEV already started; no automatic retry")
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek credential unavailable")
    frozen_run = json.loads(FREEZE.read_text(encoding="utf-8"))
    state = {"run_id": RUN_ID, "status": "running", "rows": [], "trusted_reproducer_count": 0}
    _save(OUT / "state.json", state)
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=120) as client:
            model = ChatOpenAI(
                model=MODEL, temperature=0, streaming=False,
                openai_api_base="https://api.deepseek.com", openai_api_key=settings.DEEPSEEK_API_KEY,
                max_retries=0, http_async_client=client,
            )
            for row, (instance_id, frozen, _) in zip(frozen_run["tasks"], _admitted_inputs(), strict=True):
                destination = OUT / instance_id
                status = {"instance_id": instance_id, "method": row["method"], "status": "running"}
                try:
                    _, source = route(frozen)
                    if source is None:
                        response = await budgeted_ainvoke(
                            model, [HumanMessage(content=prompt(frozen))],
                            {"configurable": {
                                "provider_ledger_path": str(LEDGER), "provider_run_id": RUN_ID,
                                "provider_task_id": instance_id,
                                "provider_total_token_ceiling": frozen_run["elastic_token_ceiling"],
                                "provider_task_token_ceiling": TASK_TOKEN_CAP,
                                "provider_max_calls_per_task": 1,
                                "provider_max_output_tokens": MAX_OUTPUT_TOKENS,
                                "provider_prompt_reserve_multiplier": 1.4,
                                "provider_disable_thinking": True,
                            }}, role="e1c2_unified_public_issue_probe_v1",
                        )
                        raw = content_text(response)
                        _save(destination / "response.json", {
                            "prompt_sha256": row["prompt_sha256"], "raw": raw,
                            "usage": usage_tokens(response),
                        })
                        source = _source(raw)
                    candidate = validate_candidate(
                        source, quote(frozen, row["method"]), frozen,
                        workspace=SOURCE / instance_id,
                    )
                    _save(destination / "candidate.json", candidate)
                    execution = execute_candidate(
                        candidate, row["image_id"], frozen["base_commit"], destination / "execution",
                        missing_optional_import=row["missing_optional_import"], repeat_nonsetup_failure=True,
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
    return {"status": "completed", "attempted": len(state["rows"]), "trusted_reproducer_count": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run"))
    args = parser.parse_args()
    if args.command == "preflight":
        value = preflight()
        if FREEZE.is_file():
            if json.loads(FREEZE.read_text(encoding="utf-8")) != value:
                raise ValueError("existing unified DEV freeze differs")
        else:
            _save(FREEZE, value)
        print(json.dumps({key: value[key] for key in (
            "model", "max_provider_calls", "total_reserve", "elastic_token_ceiling", "batch_token_cap",
        )}, ensure_ascii=False))
    else:
        print(json.dumps(asyncio.run(run()), ensure_ascii=False))


if __name__ == "__main__":
    main()
