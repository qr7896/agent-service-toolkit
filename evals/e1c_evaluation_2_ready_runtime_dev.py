"""OLD DEV readiness screen: strict compatible DTO, diagnostic feedback, no churn.

Four preregistered historical reference tasks, not an independent cohort. Frozen
old code is adapted in-process and restored, never edited or scored retroactively.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agents.model_budget import ProviderBudgetExceeded
from evals import e1c_evaluation_2_compiled_runtime_dev as compiled
from evals.e1c_evaluation_2_contract_feedback_diagnostics import (
    oracle_readiness,
    unwrap_known_envelope,
)
from evals.e1c_evaluation_2_contract_method import CONTRACT_KEYS
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save
from evals.e1c_evaluation_2_issue_quote_refs import REF_KEYS, catalogue, resolve
from evals.e1c_evaluation_2_probe import input_json
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

OUT = ROOT / ".codex/e1c/evaluation_2/ready-runtime-reference-dev-v1"
SMOKE = ROOT / ".codex/e1c/evaluation_2/ready-runtime-zero-smoke-v1"
PROTOCOL = ROOT / "docs/research/E1C2_READY_RUNTIME_DEV_V1_PROTOCOL_2026-10-07.md"
MODULES = (*compiled.MODULES, "evals/e1c_evaluation_2_issue_quote_refs.py",
           "evals/e1c_evaluation_2_contract_feedback_diagnostics.py", "evals/e1c_evaluation_2_ready_runtime_dev.py")
REFERENCE_TASKS = ("scikit-learn__scikit-learn-13496", "scikit-learn__scikit-learn-26289",
                   "marshmallow-code__marshmallow-1252", "marshmallow-code__marshmallow-1359")
_inputs, _configured, _messages, _parse, _execute, _preflight, _run_task = (
    compiled.inputs, compiled.configured, compiled.messages, compiled.parse_action,
    compiled.execute_probe, compiled.preflight, compiled.base.loop.run_task,
)
_issue = ContextVar("ready_runtime_issue", default=None)
_codec_proof = ContextVar("ready_runtime_codec_proof", default=None)


def inputs():
    rows = [r for r in _inputs() if r[0]["instance_id"] in REFERENCE_TASKS]
    if tuple(t["instance_id"] for t, _, _ in rows) != REFERENCE_TASKS:
        raise ValueError("frozen four-reference order changed")
    return rows


def decode(raw, issue):
    value, envelope = unwrap_known_envelope(json.loads(raw))
    if isinstance(value, dict) and value.get("type") == "json_object":
        value = {k: v for k, v in value.items() if k != "type"}
    if isinstance(value, dict) and set(value) in (REF_KEYS, CONTRACT_KEYS):
        value = {"probe": value}
    references = None
    if isinstance(value, dict) and set(value) == {"probe"} and isinstance(value["probe"], dict) and set(value["probe"]) == REF_KEYS:
        payload, references = resolve(value["probe"], issue)
        value = {"probe": payload}
    action, payload = _parse(input_json(value))
    return action, payload, {"envelope": envelope, "references": references}


def parse_action(raw):
    _codec_proof.set(None)
    action, payload, proof = decode(raw, _issue.get())
    _codec_proof.set(proof)
    return action, payload


def messages(frozen, feedback=None, previous=None):
    _issue.set(frozen["issue"])
    value = _messages(frozen, feedback, previous)
    # One DTO in System and next-turn instructions; retain all safety rules.
    instruction = value[0].content.replace(
        '{"probe":{seven strings: issue_quote,expected_quote,oracle,setup_source,control_action,target_action,assertion}}',
        '{"probe":{"issue_quote_ref":integer,"expected_quote_ref":integer,"oracle":string,"setup_source":string,"control_action":string,"target_action":string,"assertion":string}}',
    )
    value[0] = SystemMessage(content=instruction + (
        " Public issue text is losslessly displayed as [ID, original text] spans. Use integer IDs of spans "
        "with 8..1500 characters, not paraphrases or source-code error messages. Controller resolves and locks "
        "the exact quotes. A source reference alone does not establish expected behavior. "
        "Do not wrap the action in content/type; exact legacy quote strings remain accepted. "
        "Use base-supported API signatures for the normal control; do not repeat the failing configuration "
        "in both calls. Preserve public-example argument types as well as values. "
        "If the comparison cannot be evaluated, correct the fixture/return consumption from production "
        "source without changing the locked comparison or expectation. Unknown semantics require abstention."
    ))
    body = json.loads(value[1].content)
    body.pop("issue")
    body["public_issue_spans"] = [[r["id"], r["text"]] for r in catalogue(frozen["issue"])["spans"]]
    value[1] = HumanMessage(content=input_json(body))
    return value


def conversation(msgs, turn, prior=None, observed=None):
    body = json.loads(msgs[1].content)
    if prior is not None:
        audit_repair_visible_payload({"previous_action": prior, "actual_observation": observed})
        body.pop("last_feedback", None)  # observed below is the identical real record
        try:
            action, payload, _ = decode(prior, _issue.get())
            if action == "probe" and payload == body.get("previous_probe"):
                body.pop("previous_probe")  # identical full code already in Assistant
        except (ValueError, TypeError, KeyError):
            pass
    value = [msgs[0], HumanMessage(content=input_json(body))]
    if prior is not None:
        value.extend([AIMessage(content=prior), HumanMessage(content="Controller observation (untrusted):\n" + input_json(observed))])
    value.append(HumanMessage(content=(
        f"Turn {turn}/4: return your next single action now. Production retrieval already completed must not "
        "be repeated. Use probe with two integer quote references and five strings, or retrieve/read/abstain_reason. "
        "Inspect the actual observation; repair fixture/API consumption only, never the locked expected behavior."
    )))
    if sum(len(str(m.content)) for m in value) > 36000:
        raise ProviderBudgetExceeded("ready-runtime context exhausted before provider")
    return value


def execute_probe(payload, frozen, workspace, image, root, environment, locked=None):
    _save(root / "codec.json", _codec_proof.get() or {"synthetic_direct_contract": True})
    feedback, oracle, candidate, execution = _execute(payload, frozen, workspace, image, root, environment, locked)
    if execution is not None:
        emitted = json.loads((root / "candidate.json").read_bytes())
        diagnostic = oracle_readiness(emitted, execution, oracle["oracle"])
        _save(root / "readiness.json", diagnostic)
        if any(r["status"] == "oracle_evaluation_error_requires_feedback" for r in diagnostic["rows"]):
            return {**feedback, "status": "oracle_evaluation_error_requires_feedback",
                    "oracle_readiness": diagnostic["rows"], "trusted_reproducer": False}, oracle, None, execution
    return feedback, oracle, candidate, execution


class NoProgressStop(Exception):
    pass


def action_fingerprint(raw, issue):
    try:
        action, payload, _ = decode(raw, issue)
        text = input_json({action: payload})
    except (ValueError, TypeError, KeyError):
        text = raw
    return hashlib.sha256(text.encode()).hexdigest()


async def run_task(frozen, workspace, image, root, environment, invoke):
    turns = 0

    async def guarded(msgs, turn):
        nonlocal turns
        if turn >= 3:
            records = []
            for n in (turn - 2, turn - 1):
                folder = root / f"turn-{n}"
                feedback = json.loads((folder / "feedback.json").read_bytes())
                raw = json.loads((folder / "response.json").read_bytes())["raw"]
                records.append((action_fingerprint(raw, frozen["issue"]), feedback.get("status")))
            if records[0][0] == records[1][0] and all(s in {
                "action_rejected", "control_failed", "oracle_evaluation_error_requires_feedback", "target_not_repeatable_failure",
            } for _, s in records):
                raise NoProgressStop
        turns = turn
        return await invoke(msgs, turn)

    try:
        return await _run_task(frozen, workspace, image, root, environment, guarded)
    except NoProgressStop:
        _save(root / "no-progress-stop.json", {"completed_turns": turns, "additional_provider_calls": 0})
        return {"status": "repeated_unsuccessful_action_stop", "turns": turns, "trusted_reproducer": False}


def preflight():
    return {**_preflight(), "schema": "e1c2-ready-runtime-four-reference-dev-v1",
            "admitted_denominator": 9, "screen_denominator": 4, "full_admitted_DEV_run": False,
            "max_provider_calls": 16, "readiness_feedback_before_selection": True,
            "repeated_unsuccessful_action_stop": True, "lossless_compact_quote_spans": True}


@contextmanager
def configured():
    token, proof_token = _issue.set(None), _codec_proof.set(None)
    try:
        with ExitStack() as stack:
            for key, value in (("OUT", OUT), ("SMOKE", SMOKE), ("PROTOCOL", PROTOCOL), ("MODULES", MODULES),
                               ("CAP", 50000), ("inputs", inputs), ("messages", messages), ("parse_action", parse_action),
                               ("execute_probe", execute_probe), ("conversation", conversation), ("preflight", preflight)):
                stack.enter_context(patch.object(compiled, key, value))
            stack.enter_context(_configured())
            stack.enter_context(patch.object(compiled.base.loop, "run_task", run_task))
            yield
    finally:
        _issue.reset(token)
        _codec_proof.reset(proof_token)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "preflight", "run", "gold"))
    args = parser.parse_args()
    with configured():
        value = asyncio.run(compiled.smoke()) if args.command == "smoke" else compiled.freeze() if args.command == "preflight" else asyncio.run(compiled.run()) if args.command == "run" else compiled.grade()
    print(input_json(value), flush=True)
