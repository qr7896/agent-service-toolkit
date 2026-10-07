"""OLD DEV only: explicit API obligations before oracle lock; type provenance."""

from __future__ import annotations

import argparse
import asyncio
import json
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from langchain_core.messages import HumanMessage, SystemMessage

from evals import e1c_evaluation_2_frontier_live_dev as base
from evals.e1c_evaluation_2_api_obligation import (
    argument_provenance,
    obligations,
    verify_entrypoint,
)
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save
from evals.e1c_evaluation_2_guard_evidence_audit import guard_evidence
from evals.e1c_evaluation_2_probe import input_json

OUT = ROOT / ".codex/e1c/evaluation_2/obligation-runtime-reference-dev-v1"
SMOKE = ROOT / ".codex/e1c/evaluation_2/obligation-runtime-zero-smoke-v1"
PROTOCOL = ROOT / "docs/research/E1C2_API_OBLIGATION_DEV_V1_PROTOCOL_2026-10-07.md"
MODULES = (*base.MODULES, "evals/e1c_evaluation_2_api_obligation.py", "evals/e1c_evaluation_2_obligation_dev.py",
           "evals/e1c_evaluation_2_guard_evidence_audit.py", "evals/e1c_evaluation_2_issue_fixture_facts.py",
           "evals/e1c_evaluation_2_public_api_windows.py")
_configured, _messages, _execute, _preflight = base.configured, base.messages, base.frontier.execute_probe, base.preflight


def messages(frozen, feedback=None, previous=None):
    value = _messages(frozen, feedback, previous)
    body = json.loads(value[1].content)
    body["explicit_api_obligations"] = obligations(frozen["issue"])
    value[1] = HumanMessage(content=input_json(body))
    value[0] = SystemMessage(content=value[0].content.replace(
        "After the first statically valid probe", "After the first schema/source/explicit-API-obligation-valid probe",
    ) + (
        " Controller-derived explicit_api_obligations are limited source-bound constraints from public prose. "
        "A requested constructor keyword must be exercised at that imported constructor, not bypassed by "
        "post-initialization attribute assignment or an already-working workaround. An absent parameter in "
        "the base signature does not make the interface request untestable. Normal control must use supported API. "
        "Source guards reported in feedback still exist in the exact base; one passing synthetic input does not "
        "prove the reported condition was fixed. Argument provenance labels are controller-owned hypotheses, "
        "not original-report type facts. Inspect runtime types of your own data if needed; do not manufacture "
        "an expected value or claim unprovided setup is an observed fact. Keep the SAME seven probe fields, "
        "no extra hypothesis or obligation fields in your JSON action. No Gold/test access."
    ))
    return value


def execute_probe(payload, frozen, workspace, image, root, environment, locked=None):
    scope = verify_entrypoint(payload, frozen, workspace)
    provenance = argument_provenance(payload, frozen)
    _save(root / "api-obligation.json", scope)
    _save(root / "argument-provenance.json", provenance)
    if scope["status"] == "unfulfilled_or_unknown":
        return {"status": "action_rejected", "reason": "explicit_api_obligation_unfulfilled_or_unproven",
                "obligations": scope["rows"], "oracle_not_locked": locked is None}, locked, None, None
    feedback, oracle, candidate, execution = _execute(payload, frozen, workspace, image, root, environment, locked)
    if feedback["status"] == "target_not_repeatable_failure":
        guards = guard_evidence(payload, frozen, workspace)
        compact = [{k: r[k] for k in ("path", "line", "predicate", "source_sha256", "already_visible")}
                   for r in guards["rows"] if r["matches_public_failure_condition"]][:2]
        _save(root / "matched-failure-guards.json", {"rows": compact, "semantic_alignment_proven": False})
        feedback = {**feedback, "matched_public_failure_guards_still_present": compact,
                    "argument_provenance": provenance["rows"], "one_passing_hypothesis_is_not_general_resolution": True}
    return feedback, oracle, candidate, execution


def preflight():
    return {**_preflight(), "schema": "e1c2-api-obligation-four-reference-dev-v1",
            "explicit_entrypoint_gate_before_oracle_lock": True, "obligation_grammar_limited": True,
            "synthetic_types_not_reported_facts": True, "budget_changed_from_previous_frontier_live": False}


@contextmanager
def configured():
    with ExitStack() as stack:
        for key, value in (("OUT", OUT), ("SMOKE", SMOKE), ("PROTOCOL", PROTOCOL), ("MODULES", MODULES),
                           ("messages", messages), ("preflight", preflight)):
            stack.enter_context(patch.object(base, key, value))
        stack.enter_context(_configured())
        stack.enter_context(patch.object(base.ready.compiled.base.loop, "execute_probe", execute_probe))
        yield


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "preflight", "run", "gold"))
    args = parser.parse_args()
    with configured():
        value = asyncio.run(base.ready.compiled.smoke()) if args.command == "smoke" else base.ready.compiled.freeze() if args.command == "preflight" else asyncio.run(base.ready.compiled.run()) if args.command == "run" else base.ready.compiled.grade()
    print(input_json(value), flush=True)
