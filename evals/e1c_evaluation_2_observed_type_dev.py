"""OLD DEV only: controller type facts at public failing production guards."""

from __future__ import annotations

import argparse
import ast
import asyncio
import json
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from langchain_core.messages import SystemMessage

from evals import e1c_evaluation_2_obligation_dev as base
from evals.e1c_evaluation_2_dev_pilot import ROOT
from evals.e1c_evaluation_2_guard_type_observer import observe
from evals.e1c_evaluation_2_probe import input_json

OUT = ROOT / ".codex/e1c/evaluation_2/observed-type-reference-dev-v1"
SMOKE = ROOT / ".codex/e1c/evaluation_2/observed-type-zero-smoke-v1"
PROTOCOL = ROOT / "docs/research/E1C2_OBSERVED_TYPE_DEV_V1_PROTOCOL_2026-10-07.md"
MODULES = (*base.MODULES, "evals/e1c_evaluation_2_guard_type_observer.py", "evals/e1c_evaluation_2_observed_type_dev.py")
_configured, _messages, _execute, _preflight = base.configured, base.messages, base.execute_probe, base.preflight


def messages(frozen, feedback=None, previous=None):
    value = _messages(frozen, feedback, previous)
    value[0] = SystemMessage(content=value[0].content + (
        " Controller runtime_argument_types are actual values-free observations of your OWN generated input "
        "at the matched production guard, not a claim about unprovided original-report data. "
        "If observed type differs from your assumption, correct the assumption before declaring source fixed "
        "or unreproducible. You may propose an explicitly hypothetical, API-valid fixture consistent with "
        "public constraints and source predicate, but must not change locked behavior, claim the hypothesis "
        "is a reported fact, or bypass the normal control. No controller conversion of your input occurs."
    ))
    return value


def execute_probe(payload, frozen, workspace, image, root, environment, locked=None):
    feedback, oracle, candidate, execution = _execute(payload, frozen, workspace, image, root, environment, locked)
    if feedback["status"] == "target_not_repeatable_failure" and execution is not None:
        sites = [{"path": r["path"], "line": r["line"], "variable": r["predicate"], "source_sha256": r["source_sha256"]}
                 for r in feedback.get("matched_public_failure_guards_still_present", [])
                 if isinstance(ast.parse(r["predicate"], mode="eval").body, ast.Name)][:2]
        if sites and not execution.get("missing_optional_import"):
            emitted = json.loads((root / "candidate.json").read_bytes())
            probe = root / "execution" / (emitted["probe_sha256"] + ".py")
            report = observe(emitted, probe, sites, image, frozen["base_commit"], root / "guard-type-observation")
            if report["returncode"] == 0:
                feedback = {**feedback, "runtime_argument_types": report["records"],
                            "observation_is_own_synthetic_input_not_reported_fact": True}
            else:
                feedback = {**feedback, "type_observation_status": "instrumented_run_not_passing_no_type_fact_adopted"}
        elif sites:
            feedback = {**feedback, "type_observation_status": "optional_blocker_environment_not_supported"}
    return feedback, oracle, candidate, execution


def preflight():
    return {**_preflight(), "schema": "e1c2-observed-type-four-reference-dev-v1",
            "controller_owned_type_observation": True, "argument_values_emitted": False,
            "observer_is_not_model_safe_static_certificate": True, "budget_changed": False}


@contextmanager
def configured():
    with ExitStack() as stack:
        for key, value in (("OUT", OUT), ("SMOKE", SMOKE), ("PROTOCOL", PROTOCOL), ("MODULES", MODULES),
                           ("messages", messages), ("preflight", preflight)):
            stack.enter_context(patch.object(base, key, value))
        stack.enter_context(_configured())
        stack.enter_context(patch.object(base.base.ready.compiled.base.loop, "execute_probe", execute_probe))
        yield


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "preflight", "run", "gold"))
    args = parser.parse_args()
    with configured():
        compiled = base.base.ready.compiled
        value = asyncio.run(compiled.smoke()) if args.command == "smoke" else compiled.freeze() if args.command == "preflight" else asyncio.run(compiled.run()) if args.command == "run" else compiled.grade()
    print(input_json(value), flush=True)
