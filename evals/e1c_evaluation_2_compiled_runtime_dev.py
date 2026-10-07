"""Fresh OLD DEV only: compiled contracts, actual feedback, protected first calls.

Reuse frozen mechanisms without editing them. No native harness, test retrieval,
patching, automatic retry or independent-canary claim is introduced here.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

import httpx
from langchain_core.messages import SystemMessage

from agents.model_budget import ProviderBudgetExceeded, _prompt_text, budgeted_ainvoke
from agents.model_router import estimate_tokens
from core.settings import settings
from evals import e1c_evaluation_2_bounded_repro_dev as base
from evals.e1c_evaluation_2_bounded_repro_dev_v3 import parse_action
from evals.e1c_evaluation_2_bounded_repro_dev_v4 import conversation
from evals.e1c_evaluation_2_container_health import require_engine
from evals.e1c_evaluation_2_contract_recovery import compile_contract, failure_phase
from evals.e1c_evaluation_2_counterfactual_fast_dev import verify_workspace
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_fallback_control_audit import PINNED, PREVIOUS
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import input_json, verified_local_image
from evals.e1c_evaluation_2_raw_json import RawJsonFlash
from evals.e1c_evaluation_2_source_contract import rephase_setup
from evals.e1c_evaluation_2_source_format_control import derive_format_control

OUT = ROOT / ".codex/e1c/evaluation_2/compiled-runtime-old-dev-v1"
SMOKE = ROOT / ".codex/e1c/evaluation_2/compiled-runtime-zero-smoke-v1"
PROTOCOL = ROOT / "docs/research/E1C2_COMPILED_RUNTIME_DEV_V1_PROTOCOL_2026-10-07.md"
MODULES = (*base.MODULES, "evals/e1c_evaluation_2_bounded_action_codec.py",
           "evals/e1c_evaluation_2_bounded_repro_dev_v2.py", "evals/e1c_evaluation_2_bounded_repro_dev_v3.py",
           "evals/e1c_evaluation_2_bounded_repro_dev_v4.py", "evals/e1c_evaluation_2_contract_recovery.py",
           "evals/e1c_evaluation_2_source_format_control.py", "evals/e1c_evaluation_2_compiled_runtime_dev.py")
CAP, TASK_CAP, OUTPUT_CAP = 100000, 20000, 2000
_execute_probe, _messages = base.loop.execute_probe, base.loop.messages
COMPILER_INSTRUCTION = (
    "Contract compiler: a single comparison expression in assertion is normalized to an assert of the identical "
    "predicate; no expected values are invented. Source-proven unsupported constructor arguments can move the "
    "unchanged setup suffix into the target phase. A literal datetime normal control may be derived from verified "
    "production strptime formats; this is not proof of semantic equivalence or target format binding. "
    "Only target and oracle faithful to the public issue can become candidates. "
    "Native pytest CLI/generated fixtures are NOT actions in this version; abstain when indispensable. "
    "Neither passing controls nor stable failures establish trusted reproduction."
)


def inputs():
    if any(_sha(PREVIOUS / n) != h for n, h in PINNED.items()):
        raise ValueError("previous V4 freeze/state/ledger changed")
    old = json.loads((PREVIOUS / "freeze.json").read_bytes())
    if old["fixed_denominator"] != 12 or len(old["tasks"]) != 9:
        raise ValueError("fixed DEV12 with nine admitted inputs required")
    rows, seen = [], set()
    for task in old["tasks"]:
        iid = task["instance_id"]
        path = PREVIOUS / "inputs" / f"{iid}.json"
        if iid in seen or _sha(path) != task["input_sha256"] or verified_local_image(iid) != task["image_id"]:
            raise ValueError("duplicate or changed DEV input/image")
        initial = json.loads(path.read_bytes())
        verify_workspace(initial, SOURCE / iid)
        seen.add(iid)
        rows.append((task, initial, SOURCE / iid))
    return rows


def messages(frozen, feedback=None, previous=None):
    value = _messages(frozen, feedback, previous)
    value[0] = SystemMessage(content=value[0].content + " " + COMPILER_INSTRUCTION)
    return value


def execute_probe(payload, frozen, workspace, image, root, environment, locked=None):
    # The raw response was already saved by the loop. Compile BEFORE the lock.
    canonical, proof = compile_contract(payload, frozen, workspace)
    canonical, format_proof = derive_format_control(canonical, frozen, workspace)
    _save(root / "compiler.json", {"raw_contract": payload, "canonical_contract": canonical,
                                  "grammar_and_frontier": proof, "source_format": format_proof,
                                  "trusted_reproducer": False})
    feedback, oracle, candidate, execution = _execute_probe(
        canonical, frozen, workspace, image, root, environment, locked,
    )
    phases = []
    control = json.loads((root / "control_candidate.json").read_bytes())
    phased, _ = rephase_setup(canonical, frozen, workspace)
    for n in (1, 2):
        phases.append(failure_phase(control, json.loads((root / f"control-{n}.json").read_bytes()), phased))
    _save(root / "control_failure_phases.json", {"phases": phases, "semantic_bug_alignment_proven": False})
    return {**feedback, "comparison_wrapper_added": proof["grammar"]["wrapper_added"],
            "source_format_control_compiled": format_proof["compiled"]}, oracle, candidate, execution


@contextmanager
def configured():
    # Process-local adapter is restored even on failure; frozen source is unchanged.
    with ExitStack() as stack:
        for obj, key, value in ((base.loop, "parse_action", parse_action),
                                (base.loop, "messages", messages), (base.loop, "execute_probe", execute_probe),
                                (base, "OUT", OUT), (base, "SMOKE", SMOKE), (base, "PROTOCOL", PROTOCOL),
                                (base, "MODULES", MODULES)):
            stack.enter_context(patch.object(obj, key, value))
        yield


def reserve(initial):
    return math.ceil(estimate_tokens(_prompt_text(conversation(messages(initial), 1))) * 1.4) + OUTPUT_CAP


def protected_ceiling(tasks, index):
    return CAP - sum(t["initial_reserve"] for t in tasks[index + 1:])


def preflight():
    rows = inputs()
    require_engine(tuple(t["image_id"] for t, _, _ in rows))
    tasks = [{**task, "initial_reserve": reserve(initial)} for task, initial, _ in rows]
    if any(t["initial_reserve"] > TASK_CAP for t in tasks) or sum(t["initial_reserve"] for t in tasks) > CAP:
        raise ValueError("all initial calls cannot be protected within frozen caps")
    return {"schema": "e1c2-compiled-runtime-old-dev-v1", "fixed_denominator": 12,
            "admitted_denominator": 9, "full_admitted_DEV_run": True, "tasks": tasks,
            "previous_records": PINNED, "model": "deepseek-flash", "thinking": "disabled",
            "batch_token_cap": CAP, "task_token_cap": TASK_CAP, "max_output_tokens": OUTPUT_CAP,
            "max_provider_calls": 36, "max_calls_per_task": 4, "max_retries": 0,
            "pending_initial_reserves_protected": True, "context_chars_cap": base.loop.CONTEXT_CAP,
            "conversation_chars_cap": 36000, "native_harness_available": False,
            "method_sha256": {n: _sha(ROOT / n) for n in MODULES}, "protocol_sha256": _sha(PROTOCOL),
            "smoke_result_sha256": _sha(SMOKE / "result.json"), "smoke_freeze_sha256": _sha(SMOKE / "freeze.json"),
            "provider_calls": 0}


def freeze():
    smoke = json.loads((SMOKE / "result.json").read_bytes())
    smoke_freeze = json.loads((SMOKE / "freeze.json").read_bytes())
    if (not smoke.get("cross_repository_positive_control_gate") or smoke["provider_calls"] != 0
            or smoke_freeze["modules"] != {n: _sha(ROOT / n) for n in MODULES}):
        raise ValueError("unchanged real zero-call controls required")
    value = preflight()
    _save(OUT / "freeze.json", value)
    return value


async def run():
    frozen = json.loads((OUT / "freeze.json").read_bytes())
    if frozen != preflight():
        raise ValueError("frozen method/budget/inputs changed")
    if (OUT / "state.json").exists() or (OUT / "provider_calls.jsonl").exists():
        raise FileExistsError("run already started; no automatic retry")
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("credential unavailable")
    state = {"status": "running", "fixed_denominator": 12, "admitted_denominator": 9,
             "rows": [], "trusted_reproducer_count": 0}
    _save(OUT / "state.json", state)

    def save_state():
        (OUT / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    try:
        async with httpx.AsyncClient(trust_env=False, timeout=120) as client:
            model = RawJsonFlash(model="deepseek-flash", temperature=0, streaming=False, max_retries=0,
                                 openai_api_base="https://api.deepseek.com", openai_api_key=settings.DEEPSEEK_API_KEY,
                                 http_async_client=client).bind(response_format={"type": "json_object"})
            with configured():
                for index, (task, initial, workspace) in enumerate(inputs()):
                    iid = task["instance_id"]
                    ceiling = protected_ceiling(frozen["tasks"], index)

                    async def invoke(msgs, turn, task=task, initial=initial, workspace=workspace, ceiling=ceiling):
                        require_engine((task["image_id"],))
                        verify_workspace(initial, workspace)
                        prior, observed = None, None
                        if turn > 1:
                            folder = OUT / task["instance_id"] / f"turn-{turn - 1}"
                            prior = json.loads((folder / "response.json").read_bytes())["raw"]
                            observed = json.loads((folder / "feedback.json").read_bytes())
                        print(input_json({"task": task["instance_id"], "turn": turn, "stage": "provider_budget_check"}), flush=True)
                        return await budgeted_ainvoke(model, conversation(msgs, turn, prior, observed), {"configurable": {
                            "provider_ledger_path": str(OUT / "provider_calls.jsonl"), "provider_run_id": OUT.name,
                            "provider_task_id": task["instance_id"], "provider_total_token_ceiling": ceiling,
                            "provider_task_token_ceiling": TASK_CAP, "provider_max_calls_per_task": 4,
                            "provider_max_output_tokens": OUTPUT_CAP, "provider_prompt_reserve_multiplier": 1.4,
                            "provider_disable_thinking": True}}, role=f"e1c2_compiled_turn_{turn}")

                    try:
                        row = await base.loop.run_task(initial, workspace, task["image_id"], OUT / iid, task["environment"], invoke)
                    except ProviderBudgetExceeded as exc:
                        row = {"status": "budget_stop_no_retry", "reason": str(exc)[:300]}
                    state["rows"].append({"instance_id": iid, **row})
                    save_state()
                    print(input_json(state["rows"][-1]), flush=True)
    except Exception as exc:
        state.update({"status": "interrupted_no_auto_retry", "error_type": type(exc).__name__})
        save_state()
        raise
    state["status"] = "completed"
    save_state()
    with configured():
        base.seal()
    return state


def grade():
    with configured():
        # Existing independent Python-only scorer; no trusted-driver certificates forged.
        with patch.object(base, "preflight", preflight):
            return base.grade()


async def smoke():
    with configured():
        # Existing real positive controls remain synthetic, not model task successes.
        return await base.smoke()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "preflight", "run", "gold"))
    args = parser.parse_args()
    value = asyncio.run(smoke()) if args.command == "smoke" else freeze() if args.command == "preflight" else asyncio.run(run()) if args.command == "run" else grade()
    print(input_json(value), flush=True)
