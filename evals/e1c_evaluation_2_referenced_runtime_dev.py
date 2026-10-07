"""Separate fresh OLD DEV experiment with exact public-issue quote references."""

from __future__ import annotations

import argparse
import asyncio
import json
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from unittest.mock import patch

from langchain_core.messages import HumanMessage, SystemMessage

from evals import e1c_evaluation_2_compiled_runtime_dev as compiled
from evals.e1c_evaluation_2_contract_method import CONTRACT_KEYS
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save
from evals.e1c_evaluation_2_issue_quote_refs import REF_KEYS, catalogue, resolve
from evals.e1c_evaluation_2_probe import input_json

OUT = ROOT / ".codex/e1c/evaluation_2/referenced-runtime-old-dev-v1"
SMOKE = ROOT / ".codex/e1c/evaluation_2/referenced-runtime-zero-smoke-v1"
PROTOCOL = ROOT / "docs/research/E1C2_REFERENCED_RUNTIME_DEV_V1_PROTOCOL_2026-10-07.md"
MODULES = (*compiled.MODULES, "evals/e1c_evaluation_2_issue_quote_refs.py",
           "evals/e1c_evaluation_2_referenced_runtime_dev.py")
_configured, _messages, _parse, _execute, _conversation = (
    compiled.configured, compiled.messages, compiled.parse_action, compiled.execute_probe, compiled.conversation,
)
_preflight = compiled.preflight
_issue = ContextVar("public_issue_for_quote_refs", default=None)
_reference_proof = ContextVar("quote_reference_proof", default=None)


def messages(frozen, feedback=None, previous=None):
    value = _messages(frozen, feedback, previous)
    _issue.set(frozen["issue"])
    body = json.loads(value[1].content)
    body.pop("issue")
    body["public_issue_catalogue"] = catalogue(frozen["issue"])
    value[1] = HumanMessage(content=input_json(body))
    value[0] = SystemMessage(content=value[0].content + (
        " Public issue text is displayed losslessly as numbered spans, not replaced by a summary. "
        "For your probe, prefer this EXACT seven-field object: issue_quote_ref and expected_quote_ref are integer "
        "IDs of quote_eligible spans; oracle, setup_source, control_action, target_action, assertion are strings. "
        "The controller resolves IDs to the original text and locks the resulting quotes and oracle. "
        "Never invent an exception message or quote from production source as public expectation. "
        "The expected reference must actually support the claimed behavior; a valid ID alone proves nothing. "
        "Do not repeat an invalid quote; legacy exact string quotes remain accepted for compatibility."
    ))
    return value


def parse_action(raw):
    _reference_proof.set(None)
    value = json.loads(raw)
    if isinstance(value, dict) and value.get("type") == "json_object":
        value = {k: v for k, v in value.items() if k != "type"}
    if isinstance(value, dict) and set(value) == REF_KEYS:
        value = {"probe": value}
    if isinstance(value, dict) and set(value) == {"probe"} and isinstance(value["probe"], dict) and set(value["probe"]) == REF_KEYS:
        canonical, proof = resolve(value["probe"], _issue.get())
        _reference_proof.set(proof)
        value = {"probe": canonical}
    if isinstance(value, dict) and set(value) == CONTRACT_KEYS:
        value = {"probe": value}
    return _parse(input_json(value))


def execute_probe(payload, frozen, workspace, image, root, environment, locked=None):
    proof = _reference_proof.get()
    if proof is not None:
        if proof["issue_sha256"] != catalogue(frozen["issue"])["issue_sha256"]:
            raise ValueError("public issue reference identity changed")
        _save(root / "quote_references.json", proof)
    return _execute(payload, frozen, workspace, image, root, environment, locked)


def conversation(msgs, turn, prior=None, observed=None):
    value = _conversation(msgs, turn, prior, observed)
    value[-1] = HumanMessage(content=value[-1].content.replace(
        "seven-field positive-control probe", "positive-control probe with five strings and two public quote-reference IDs",
    ))
    # Recheck after the changed last instruction, before any provider call.
    if sum(len(str(m.content)) for m in value) > 36000:
        from agents.model_budget import ProviderBudgetExceeded

        raise ProviderBudgetExceeded("referenced conversation context exhausted; no provider call")
    return value


def preflight():
    return {**_preflight(), "schema": "e1c2-referenced-runtime-old-dev-v1",
            "public_issue_rendering_lossless": True, "exact_quote_reference_resolution": True,
            "semantic_alignment_proven_by_quote_ids": False}


@contextmanager
def configured():
    token, proof_token = _issue.set(None), _reference_proof.set(None)
    try:
        with ExitStack() as stack:
            for key, value in (("OUT", OUT), ("SMOKE", SMOKE), ("PROTOCOL", PROTOCOL), ("MODULES", MODULES),
                               ("messages", messages), ("parse_action", parse_action), ("execute_probe", execute_probe),
                               ("conversation", conversation), ("preflight", preflight)):
                stack.enter_context(patch.object(compiled, key, value))
            stack.enter_context(_configured())
            yield
    finally:
        _issue.reset(token)
        _reference_proof.reset(proof_token)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "preflight", "run", "gold"))
    args = parser.parse_args()
    with configured():
        value = asyncio.run(compiled.smoke()) if args.command == "smoke" else compiled.freeze() if args.command == "preflight" else asyncio.run(compiled.run()) if args.command == "run" else compiled.grade()
    print(input_json(value), flush=True)
