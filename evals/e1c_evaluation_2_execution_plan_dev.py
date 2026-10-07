"""OLD DEV: source-bound execution plans; no input repair or trust promotion."""

from __future__ import annotations

import argparse
import ast
import asyncio
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from langchain_core.messages import HumanMessage

from agents.model_budget import ProviderBudgetExceeded
from evals import e1c_evaluation_2_unified_codec_dev as base
from evals.e1c_evaluation_2_contract_recovery import tree_sha
from evals.e1c_evaluation_2_contrast_audit import contrast_evidence, truth_guard_evidence
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save
from evals.e1c_evaluation_2_probe import input_json

OUT = ROOT / ".codex/e1c/evaluation_2/execution-plan-reference-dev-v1"
SMOKE = ROOT / ".codex/e1c/evaluation_2/execution-plan-zero-smoke-v1"
PROTOCOL = ROOT / "docs/research/E1C2_EXECUTION_PLAN_DEV_V1_PROTOCOL_2026-10-07.md"
MODULES = (*base.MODULES, "evals/e1c_evaluation_2_contrast_audit.py", "evals/e1c_evaluation_2_execution_plan_dev.py")
_compiled = base.base._compiled
_configured, _execute, _preflight, _conversation = (
    base.configured, base.base.execute_probe, base.preflight, base.base.conversation,
)


def execution_plan(payload, feedback):
    contrast = contrast_evidence(payload)
    demands = []
    for row in feedback.get("matched_public_failure_guards_still_present", [])[:2]:
        semantics = truth_guard_evidence(row["predicate"])
        if semantics["supported"]:
            demands.append({**{k: row[k] for k in ("path", "line", "source_sha256")}, **semantics})
    status = feedback["status"]
    return {"schema": "e1c2-source-bound-execution-plan-v1", "contrast": contrast,
            "target_program_ast_sha256": tree_sha(ast.parse(payload["setup_source"] + "\n" + payload["target_action"])),
            "oracle_ast_sha256": tree_sha(ast.parse(payload["assertion"])),
            "next_evidence": "supported_normal_configuration" if status == "control_failed" else
                "unexplored_source_consistent_input_hypothesis" if status == "target_not_repeatable_failure" and demands else "none",
            "implicit_operations": demands,
            "observed_own_argument_types": feedback.get("runtime_argument_types", []),
            "one_passing_input_not_exhaustive": status == "target_not_repeatable_failure",
            "controller_modified_probe": False, "input_hypothesis_is_not_report_fact": True,
            "semantic_alignment_proven": False, "trusted_reproducer": False}


def execute_probe(payload, frozen, workspace, image, root, environment, locked=None):
    result = _execute(payload, frozen, workspace, image, root, environment, locked)
    feedback, oracle, candidate, execution = result
    plan = execution_plan(payload, feedback)
    _save(root / "execution-plan.json", plan)
    if plan["next_evidence"] != "none":
        feedback = {**feedback, "next_execution_plan": plan}
    return feedback, oracle, candidate, execution


def conversation(msgs, turn, prior=None, observed=None):
    value = _conversation(msgs, turn, prior, observed)
    value[-1] = HumanMessage(content=value[-1].content + (
        " Consume next_execution_plan when present: supported_normal_configuration requires a normal "
        "production configuration, not the same failing configuration. An unexplored source-consistent input "
        "hypothesis requires reasoning about the recorded implicit operation and observed OWN type; no explicit "
        "raise is needed for a type protocol to fail. Propose and execute an API-valid hypothesis if supported, "
        "without claiming it is original-report data. Unknown desired behavior still requires abstention. "
        "Do not infer exhaustive impossibility from one passing input. Keep the same action DTO and locked oracle."
    ))
    if sum(len(str(m.content)) for m in value) > 36000:
        raise ProviderBudgetExceeded("execution plan context exhausted before provider")
    return value


def preflight():
    return {**_preflight(), "schema": "e1c2-execution-plan-four-reference-dev-v1",
            "source_bound_execution_plan_feedback": True, "controller_input_conversion": False,
            "diagnostics_do_not_promote_trust": True, "budget_changed": False}


@contextmanager
def configured():
    with ExitStack() as stack:
        for key, value in (("OUT", OUT), ("SMOKE", SMOKE), ("PROTOCOL", PROTOCOL), ("MODULES", MODULES),
                           ("preflight", preflight)):
            stack.enter_context(patch.object(base, key, value))
        stack.enter_context(_configured())
        stack.enter_context(patch.object(_compiled.base.loop, "execute_probe", execute_probe))
        stack.enter_context(patch.object(_compiled, "conversation", conversation))
        yield


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "preflight", "run", "gold"))
    args = parser.parse_args()
    with configured():
        value = asyncio.run(_compiled.smoke()) if args.command == "smoke" else _compiled.freeze() if args.command == "preflight" else asyncio.run(_compiled.run()) if args.command == "run" else _compiled.grade()
    print(input_json(value), flush=True)
