"""Preserve the complete adapter chain across the runner's nested configuration."""

from __future__ import annotations

import argparse
import asyncio
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from evals import e1c_evaluation_2_execution_plan_dev as base
from evals.e1c_evaluation_2_dev_pilot import ROOT
from evals.e1c_evaluation_2_probe import input_json

OUT = ROOT / ".codex/e1c/evaluation_2/execution-plan-reference-dev-v2"
SMOKE = ROOT / ".codex/e1c/evaluation_2/execution-plan-zero-smoke-v2"
PROTOCOL = ROOT / "docs/research/E1C2_EXECUTION_PLAN_DEV_V2_PROTOCOL_2026-10-07.md"
MODULES = (*base.MODULES, "evals/e1c_evaluation_2_execution_plan_dev_v2.py")
_configured, _preflight = base.configured, base.preflight


def preflight():
    return {**_preflight(), "schema": "e1c2-execution-plan-four-reference-dev-v2",
            "adapter_chain_preserved_in_nested_runner_configuration": True}


@contextmanager
def configured():
    with ExitStack() as stack:
        for key, value in (("OUT", OUT), ("SMOKE", SMOKE), ("PROTOCOL", PROTOCOL), ("MODULES", MODULES),
                           ("preflight", preflight)):
            stack.enter_context(patch.object(base, key, value))
        stack.enter_context(_configured())
        # Inner compiled.configured() binds its own execute_probe, not the outer
        # loop hook. Patch that owner too; captured delegates prevent recursion.
        stack.enter_context(patch.object(base._compiled, "execute_probe", base.execute_probe))
        yield


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "preflight", "run", "gold"))
    args = parser.parse_args()
    with configured():
        runner = base._compiled
        value = asyncio.run(runner.smoke()) if args.command == "smoke" else runner.freeze() if args.command == "preflight" else asyncio.run(runner.run()) if args.command == "run" else runner.grade()
    print(input_json(value), flush=True)
