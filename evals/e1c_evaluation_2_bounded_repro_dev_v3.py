"""Separate trial: normalize only known JSON-format metadata, preserve action."""

from __future__ import annotations

import argparse
import asyncio
import json

from evals import e1c_evaluation_2_bounded_repro_dev as base
from evals.e1c_evaluation_2_bounded_action_codec import parse_action as typed_parse
from evals.e1c_evaluation_2_bounded_repro_dev_v2 import budgeted_invoke
from evals.e1c_evaluation_2_contract_method import CONTRACT_KEYS
from evals.e1c_evaluation_2_dev_pilot import ROOT
from evals.e1c_evaluation_2_probe import input_json

OUT = ROOT / ".codex/e1c/evaluation_2/bounded-runtime-dev-v3"
SMOKE = ROOT / ".codex/e1c/evaluation_2/bounded-runtime-zero-smoke-v3"
PROTOCOL = ROOT / "docs/research/E1C2_BOUNDED_RUNTIME_DEV_V3_PROTOCOL_2026-10-07.md"
_preflight = base.preflight
MODULES = (*base.MODULES, "evals/e1c_evaluation_2_bounded_action_codec.py",
           "evals/e1c_evaluation_2_bounded_repro_dev_v2.py", "evals/e1c_evaluation_2_bounded_repro_dev_v3.py")


def parse_action(raw):
    value = json.loads(raw)
    if isinstance(value, dict) and value.get("type") == "json_object":
        value = {k: v for k, v in value.items() if k != "type"}
        if set(value) == CONTRACT_KEYS:
            value = {"probe": value}
    return typed_parse(input_json(value))


def configure():
    base.OUT, base.SMOKE, base.PROTOCOL, base.MODULES = OUT, SMOKE, PROTOCOL, MODULES
    base.loop.parse_action, base.budgeted_ainvoke, base.preflight = parse_action, budgeted_invoke, preflight


def preflight():
    configure()
    value = _preflight()
    for task in value["tasks"]:
        task["initial_reserve"] -= 200
        if task["initial_reserve"] > 20000:
            raise ValueError("initial reserve exceeds reduced cap")
    return {**value, "schema": "e1c2-bounded-runtime-old-dev-screen-v3", "batch_token_cap": 60000,
            "task_token_cap": 20000, "max_output_tokens": 2000, "known_json_format_metadata_normalized": True,
            "prompts_or_source_inputs_changed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "preflight", "run", "gold"))
    args = parser.parse_args()
    configure()
    value = asyncio.run(base.smoke()) if args.command == "smoke" else base.freeze() if args.command == "preflight" else asyncio.run(base.run()) if args.command == "run" else base.grade()
    print(json.dumps(value, ensure_ascii=False))
