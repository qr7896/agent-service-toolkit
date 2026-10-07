"""Separate old-DEV trial with strict typed-action normalization and lower cap."""

from __future__ import annotations

import argparse
import asyncio
import json

from evals import e1c_evaluation_2_bounded_repro_dev as base
from evals.e1c_evaluation_2_bounded_action_codec import parse_action
from evals.e1c_evaluation_2_dev_pilot import ROOT

OUT = ROOT / ".codex/e1c/evaluation_2/bounded-runtime-dev-v2"
SMOKE = ROOT / ".codex/e1c/evaluation_2/bounded-runtime-zero-smoke-v2"
PROTOCOL = ROOT / "docs/research/E1C2_BOUNDED_RUNTIME_DEV_V2_PROTOCOL_2026-10-07.md"
_preflight, _invoke = base.preflight, base.budgeted_ainvoke
MODULES = (*base.MODULES, "evals/e1c_evaluation_2_bounded_action_codec.py", "evals/e1c_evaluation_2_bounded_repro_dev_v2.py")


async def budgeted_invoke(model, messages, config, *, role):
    conf = {**config["configurable"], "provider_total_token_ceiling": 60000,
            "provider_task_token_ceiling": 20000, "provider_max_output_tokens": 2000}
    return await _invoke(model, messages, {"configurable": conf}, role=role)


def configure():
    base.OUT, base.SMOKE, base.PROTOCOL, base.MODULES = OUT, SMOKE, PROTOCOL, MODULES
    base.loop.parse_action, base.budgeted_ainvoke, base.preflight = parse_action, budgeted_invoke, preflight


def preflight():
    configure()
    value = _preflight()
    for task in value["tasks"]:
        task["initial_reserve"] -= 200
        if task["initial_reserve"] > 20000:
            raise ValueError("v2 initial reserve exceeds reduced task cap")
    return {**value, "schema": "e1c2-bounded-runtime-old-dev-screen-v2",
            "batch_token_cap": 60000, "task_token_cap": 20000, "max_output_tokens": 2000,
            "strict_typed_action_normalization": True, "prompts_or_source_inputs_changed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "preflight", "run", "gold"))
    args = parser.parse_args()
    configure()
    value = asyncio.run(base.smoke()) if args.command == "smoke" else base.freeze() if args.command == "preflight" else asyncio.run(base.run()) if args.command == "run" else base.grade()
    print(json.dumps(value, ensure_ascii=False))
