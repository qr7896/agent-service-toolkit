"""Actual action/observation history and explicit next-turn request, OLD DEV only."""

from __future__ import annotations

import argparse
import asyncio
import json

from langchain_core.messages import AIMessage, HumanMessage

from agents.model_budget import ProviderBudgetExceeded
from evals import e1c_evaluation_2_bounded_repro_dev as base
from evals.e1c_evaluation_2_bounded_repro_dev_v2 import budgeted_invoke as capped_invoke
from evals.e1c_evaluation_2_bounded_repro_dev_v3 import parse_action
from evals.e1c_evaluation_2_dev_pilot import ROOT
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

OUT = ROOT / ".codex/e1c/evaluation_2/bounded-runtime-dev-v4"
SMOKE = ROOT / ".codex/e1c/evaluation_2/bounded-runtime-zero-smoke-v4"
PROTOCOL = ROOT / "docs/research/E1C2_BOUNDED_RUNTIME_DEV_V4_PROTOCOL_2026-10-07.md"
_preflight = base.preflight
MODULES = (*base.MODULES, "evals/e1c_evaluation_2_bounded_action_codec.py",
           "evals/e1c_evaluation_2_bounded_repro_dev_v2.py", "evals/e1c_evaluation_2_bounded_repro_dev_v3.py",
           "evals/e1c_evaluation_2_bounded_repro_dev_v4.py")


def conversation(messages, turn, prior=None, observed=None):
    value = list(messages)
    if prior is not None:
        audit_repair_visible_payload({"previous_action": prior, "actual_observation": observed})
        value.extend([AIMessage(content=prior), HumanMessage(content="Controller observation (untrusted data):\n" + json.dumps(observed, ensure_ascii=False))])
    value.append(HumanMessage(content=(
        f"This is controller turn {turn}/4. Produce your next action now, not a schema or a repeat of the input. "
        "The previous requested retrieval has already completed; inspect its returned production windows and observation. "
        "Do not repeat the same retrieval. If a qualified symbol was not found, consider the unqualified symbol or abstain. "
        "If the evidence suffices, submit the seven-field positive-control probe; otherwise read another exposed source "
        "window or request a different symbol. Preserve the locked expected behavior. Return only your one JSON action."
    )))
    if sum(len(str(m.content)) for m in value) > 36000:
        raise ProviderBudgetExceeded("bounded conversation context exhausted; no provider call")
    return value


async def budgeted_invoke(model, messages, config, *, role):
    turn = int(role.rsplit("_", 1)[-1])
    prior, observed = None, None
    if turn > 1:
        task = config["configurable"]["provider_task_id"]
        folder = OUT / task / f"turn-{turn - 1}"
        prior = json.loads((folder / "response.json").read_bytes())["raw"]
        observed = json.loads((folder / "feedback.json").read_bytes())
    return await capped_invoke(model, conversation(messages, turn, prior, observed), config, role=role)


def configure():
    base.OUT, base.SMOKE, base.PROTOCOL, base.MODULES = OUT, SMOKE, PROTOCOL, MODULES
    base.loop.parse_action, base.budgeted_ainvoke, base.preflight = parse_action, budgeted_invoke, preflight


def preflight():
    configure()
    value = _preflight()
    for task, (_, initial, _) in zip(value["tasks"], base.inputs(), strict=True):
        import math

        from agents.model_budget import _prompt_text
        from agents.model_router import estimate_tokens

        task["initial_reserve"] = math.ceil(estimate_tokens(_prompt_text(conversation(base.loop.messages(initial), 1))) * 1.4) + 2000
        if task["initial_reserve"] > 20000:
            raise ValueError("initial reserve exceeds reduced cap")
    return {**value, "schema": "e1c2-bounded-runtime-old-dev-screen-v4", "batch_token_cap": 60000,
            "task_token_cap": 20000, "max_output_tokens": 2000, "conversation_chars_cap": 36000,
            "actual_previous_action_and_observation": True, "explicit_turn_and_next_action_request": True,
            "source_input_method_changed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "preflight", "run", "gold"))
    args = parser.parse_args()
    configure()
    value = asyncio.run(base.smoke()) if args.command == "smoke" else base.freeze() if args.command == "preflight" else asyncio.run(base.run()) if args.command == "run" else base.grade()
    print(json.dumps(value, ensure_ascii=False))
