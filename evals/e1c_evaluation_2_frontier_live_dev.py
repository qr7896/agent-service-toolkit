"""Fresh OLD DEV reference screen with execution-bound setup frontier, Flash only."""

from __future__ import annotations

import argparse
import asyncio
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from langchain_core.messages import SystemMessage

from evals import e1c_evaluation_2_ready_runtime_dev as ready
from evals import e1c_evaluation_2_runtime_frontier_zero as frontier
from evals.e1c_evaluation_2_dev_pilot import ROOT
from evals.e1c_evaluation_2_probe import input_json

OUT = ROOT / ".codex/e1c/evaluation_2/frontier-runtime-reference-dev-v1"
SMOKE = ROOT / ".codex/e1c/evaluation_2/frontier-runtime-zero-smoke-v1"
PROTOCOL = ROOT / "docs/research/E1C2_FRONTIER_LIVE_DEV_V1_PROTOCOL_2026-10-07.md"
MODULES = (*frontier.MODULES, "evals/e1c_evaluation_2_frontier_live_dev.py")
_configured, _preflight, _messages = ready.configured, ready.preflight, ready.messages


def messages(frozen, feedback=None, previous=None):
    value = _messages(frozen, feedback, previous)
    value[0] = SystemMessage(content=value[0].content + (
        " The controller may relocate a repeatable failing setup assignment into target after proving the full "
        "target program AST unchanged and normal-control free names disjoint. Alias/global independence is not "
        "proven. If target passes, inspect the reported argument types and production branch before further "
        "retrieval; never change the expected behavior to manufacture a failure."
    ))
    return value


def preflight():
    return {**_preflight(), "schema": "e1c2-frontier-runtime-four-reference-dev-v1",
            "execution_bound_setup_frontier": True, "task_cap_adjusted_from": 20000,
            "isolated_single_factor_causal_comparison": False}


@contextmanager
def configured():
    with ExitStack() as stack:
        for key, value in (("OUT", OUT), ("SMOKE", SMOKE), ("PROTOCOL", PROTOCOL), ("MODULES", MODULES),
                           ("execute_probe", frontier.execute_probe), ("messages", messages), ("preflight", preflight)):
            stack.enter_context(patch.object(ready, key, value))
        stack.enter_context(_configured())
        # Existing conservative reserve is retained; only the NEW task cap changes.
        stack.enter_context(patch.object(ready.compiled, "TASK_CAP", 24000))
        yield


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "preflight", "run", "gold"))
    args = parser.parse_args()
    with configured():
        value = asyncio.run(ready.compiled.smoke()) if args.command == "smoke" else ready.compiled.freeze() if args.command == "preflight" else asyncio.run(ready.compiled.run()) if args.command == "run" else ready.compiled.grade()
    print(input_json(value), flush=True)
