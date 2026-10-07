"""Frozen three-repository OLD DEV screen for the restricted runtime loop."""

from __future__ import annotations

import argparse
import asyncio
import json
import math

import httpx
from langchain_core.messages import AIMessage

from agents.model_budget import ProviderBudgetExceeded, _prompt_text, budgeted_ainvoke
from agents.model_router import estimate_tokens
from core.settings import settings
from evals import e1c_evaluation_2_bounded_repro_loop as loop
from evals.e1c_evaluation_2_container_health import require_engine
from evals.e1c_evaluation_2_counterfactual_fast_dev import verify_workspace
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_fallback_control_audit import PINNED, PREVIOUS
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import input_json, verified_local_image
from evals.e1c_evaluation_2_raw_json import RawJsonFlash

OUT = ROOT / ".codex/e1c/evaluation_2/bounded-runtime-dev-v1"
SMOKE = ROOT / ".codex/e1c/evaluation_2/bounded-runtime-zero-smoke-v1"
PROTOCOL = ROOT / "docs/research/E1C2_BOUNDED_RUNTIME_DEV_V1_PROTOCOL_2026-10-07.md"
MODULES = ("evals/e1c_evaluation_2_bounded_repro_loop.py", "evals/e1c_evaluation_2_bounded_repro_dev.py",
           "evals/e1c_evaluation_2_contract_method.py", "evals/e1c_evaluation_2_counterfactual_contract.py",
           "evals/e1c_evaluation_2_source_contract.py", "evals/e1c_evaluation_2_probe.py",
           "evals/e1c_evaluation_2_production_coverage.py", "evals/e1c_blind_evidence.py",
           "evals/e1c_blind_boundary.py", "evals/e1c_strict_v5_boundary.py",
           "evals/e1c_evaluation_2_execution_contract.py", "evals/e1c_evaluation_2_container_health.py",
           "evals/e1c_evaluation_2_raw_json.py", "evals/e1c_evaluation_2_dev_pilot.py",
           "evals/e1c_evaluation_2_issue_input.py", "evals/e1c_evaluation_2_counterfactual_fast_dev.py",
           "evals/e1c_evaluation_2_fallback_control_audit.py", "src/agents/model_budget.py", "src/agents/model_router.py")


def inputs():
    if any(_sha(PREVIOUS / n) != h for n, h in PINNED.items()):
        raise ValueError("previous V4 freeze/state/ledger changed")
    old = json.loads((PREVIOUS / "freeze.json").read_bytes())
    rows, seen = [], set()
    for task in old["tasks"]:
        iid = task["instance_id"]
        repo = iid.split("__", 1)[0]
        if repo in seen:
            continue
        path = PREVIOUS / "inputs" / f"{iid}.json"
        if _sha(path) != task["input_sha256"] or verified_local_image(iid) != task["image_id"]:
            raise ValueError("old DEV input/image identity changed")
        frozen = json.loads(path.read_bytes())
        verify_workspace(frozen, SOURCE / iid)
        seen.add(repo)
        rows.append((task, frozen, SOURCE / iid))
    if old["fixed_denominator"] != 12 or len(rows) != 3:
        raise ValueError("expected DEV12, first admitted task per each of three repositories")
    return rows


def preflight():
    rows = inputs()
    require_engine(tuple(t["image_id"] for t, _, _ in rows))
    tasks = []
    for task, frozen, _ in rows:
        reserve = math.ceil(estimate_tokens(_prompt_text(loop.messages(frozen))) * 1.4) + 2200
        if reserve > 26000:
            raise ValueError("initial prompt reserve exceeds task cap")
        tasks.append({**task, "initial_reserve": reserve})
    return {"schema": "e1c2-bounded-runtime-old-dev-screen-v1", "fixed_denominator": 12,
            "screen_denominator": 3, "full_DEV12_run": False, "tasks": tasks, "previous_records": PINNED,
            "model": "deepseek-flash", "thinking": "disabled", "max_provider_calls": 12,
            "max_calls_per_task": 4, "batch_token_cap": 80000, "task_token_cap": 26000,
            "max_output_tokens": 2200, "max_retries": 0, "context_chars_cap": loop.CONTEXT_CAP,
            "method_sha256": {n: _sha(ROOT / n) for n in MODULES}, "protocol_sha256": _sha(PROTOCOL),
            "smoke_result_sha256": _sha(SMOKE / "result.json"), "smoke_freeze_sha256": _sha(SMOKE / "freeze.json"), "provider_calls": 0}


def freeze():
    smoke = json.loads((SMOKE / "result.json").read_bytes())
    if not smoke.get("cross_repository_positive_control_gate") or smoke["provider_calls"] != 0:
        raise ValueError("real isolated zero-provider controls required")
    smoke_freeze = json.loads((SMOKE / "freeze.json").read_bytes())
    if smoke_freeze["modules"] != {n: _sha(ROOT / n) for n in MODULES}:
        raise ValueError("smoke method changed; cannot use its result as the gate")
    value = preflight()
    path = OUT / "freeze.json"
    if path.exists():
        if json.loads(path.read_bytes()) != value:
            raise ValueError("new method changed after freeze")
    else:
        _save(path, value)
    return value


def seal():
    value = {p.relative_to(OUT).as_posix(): _sha(p) for p in sorted(OUT.rglob("*"))
             if p.is_file() and p.name != "generation-seal.json" and "gold-discrimination" not in p.parts}
    _save(OUT / "generation-seal.json", {"files": value, "selection_before_grader": True})


async def run():
    frozen_run = json.loads((OUT / "freeze.json").read_bytes())
    if frozen_run != preflight():
        raise ValueError("frozen runtime method changed")
    if (OUT / "state.json").exists() or (OUT / "provider_calls.jsonl").exists():
        raise FileExistsError("run already started; no automatic retry")
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("credential unavailable")
    state = {"status": "running", "fixed_denominator": 12, "screen_denominator": 3, "rows": [], "trusted_reproducer_count": 0}
    state_path = OUT / "state.json"
    _save(state_path, state)
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=120) as client:
            model = RawJsonFlash(model="deepseek-flash", temperature=0, streaming=False, max_retries=0,
                                 openai_api_base="https://api.deepseek.com", openai_api_key=settings.DEEPSEEK_API_KEY,
                                 http_async_client=client).bind(response_format={"type": "json_object"})
            for task, initial, workspace in inputs():
                iid, image = task["instance_id"], task["image_id"]

                async def invoke(messages, turn, task=task, initial=initial, workspace=workspace):
                    require_engine((task["image_id"],))
                    verify_workspace(initial, workspace)
                    return await budgeted_ainvoke(model, messages, {"configurable": {
                        "provider_ledger_path": str(OUT / "provider_calls.jsonl"), "provider_run_id": OUT.name,
                        "provider_task_id": task["instance_id"], "provider_total_token_ceiling": 80000,
                        "provider_task_token_ceiling": 26000, "provider_max_calls_per_task": 4,
                        "provider_max_output_tokens": 2200, "provider_prompt_reserve_multiplier": 1.4,
                        "provider_disable_thinking": True}}, role=f"e1c2_bounded_turn_{turn}")

                try:
                    row = await loop.run_task(initial, workspace, image, OUT / iid, task["environment"], invoke)
                except ProviderBudgetExceeded:
                    row = {"status": "budget_stop_no_retry"}
                state["rows"].append({"instance_id": iid, **row})
                state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(input_json(state["rows"][-1]), flush=True)
    except Exception as exc:
        state.update({"status": "interrupted_no_auto_retry", "error_type": type(exc).__name__})
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise
    state["status"] = "completed"
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    seal()
    return state


def grade():
    manifest = json.loads((OUT / "generation-seal.json").read_bytes())
    if any(_sha(OUT / n) != h for n, h in manifest["files"].items()):
        raise ValueError("generated artifacts changed before independent scoring")
    from evals import e1c_evaluation_2_unified_dev_v2_gold as grader

    grader.base.OUT, grader.base.FREEZE, grader.base.preflight = OUT, OUT / "freeze.json", preflight
    grader.OUT = OUT / "gold-discrimination"
    return grader.run()


async def smoke():
    if SMOKE.exists():
        raise FileExistsError("smoke already started; preserve artifacts")
    rows = inputs()
    require_engine(tuple(t["image_id"] for t, _, _ in rows))
    _save(SMOKE / "freeze.json", {"modules": {n: _sha(ROOT / n) for n in MODULES}, "provider_calls": 0,
                                 "synthetic_not_task_score": True})
    reports = []
    examples = {"scikit-learn": ("IsolationForest", "from sklearn.ensemble import IsolationForest",
                                 "result = IsolationForest(n_estimators=2, random_state=0)"),
                "marshmallow": ("Schema", "from marshmallow import Schema", "result = Schema().dump({})")}
    for task, initial, workspace in rows:
        name = "scikit-learn" if "scikit-learn" in task["instance_id"] else "marshmallow" if "marshmallow" in task["instance_id"] else None
        if name is None:
            continue
        symbol, setup, call = examples[name]
        synthetic = {**initial, "issue": "Synthetic mechanism check: a supported production API call should complete."}
        payload = {"issue_quote": "supported production API call", "expected_quote": "should complete",
                   "oracle": "call_completes", "setup_source": setup, "control_action": call,
                   "target_action": call, "assertion": ""}
        actions = [{"retrieve": symbol}, {"probe": payload}, {"abstain_reason": "synthetic passing call is not a bug witness"}]
        observed = []

        async def invoke(messages, turn):
            observed.append(json.loads(messages[-1].content)["last_feedback"])
            return AIMessage(content=input_json(actions[turn - 1]), usage_metadata={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0})

        root = SMOKE / name
        result = await loop.run_task(synthetic, workspace, task["image_id"], root, task["environment"], invoke)
        controls = [json.loads((root / "turn-2" / f"control-{n}.json").read_bytes()) for n in (1, 2)]
        passed = all(loop.checked_execution(e) for e in controls)
        if not passed or observed[-1]["status"] != "target_not_repeatable_failure" or result["status"] != "abstained":
            raise ValueError("real positive control/feedback loop gate failed")
        reports.append({"repository": name, "two_base_controls_pass": passed, "feedback_consumed": True,
                        "not_selected_as_bug": True, "turns": result["turns"]})
        print(input_json(reports[-1]), flush=True)
    value = {"schema": "e1c2-bounded-runtime-zero-smoke-v1", "cross_repository_positive_control_gate": len(reports) == 2,
             "provider_calls": 0, "synthetic_not_task_score": True, "rows": reports}
    _save(SMOKE / "result.json", value)
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "preflight", "run", "gold"))
    args = parser.parse_args()
    value = asyncio.run(smoke()) if args.command == "smoke" else freeze() if args.command == "preflight" else asyncio.run(run()) if args.command == "run" else grade()
    print(json.dumps(value, ensure_ascii=False))
