"""OLD DEV: public-report facts and explicitly labeled completion hypotheses."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from langchain_core.messages import HumanMessage, SystemMessage

from agents.model_budget import ProviderBudgetExceeded
from evals import e1c_evaluation_2_expectation_dev as base
from evals.e1c_evaluation_2_api_obligation import obligations
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save
from evals.e1c_evaluation_2_issue_quote_refs import catalogue
from evals.e1c_evaluation_2_probe import input_json
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

OUT = ROOT / ".codex/e1c/evaluation_2/report-anchor-reference-dev-v1"
SMOKE = ROOT / ".codex/e1c/evaluation_2/report-anchor-zero-smoke-v1"
PROTOCOL = ROOT / "docs/research/E1C2_REPORT_ANCHOR_DEV_V1_PROTOCOL_2026-10-07.md"
MODULES = (*base.MODULES, "evals/e1c_evaluation_2_report_anchor_dev.py")
_compiled = base._compiled
_configured, _messages, _execute, _preflight, _conversation = (
    base.configured, base.messages, base.execute_probe, base.preflight, base.base.base.conversation,
)


def report_anchors(issue):
    catalog = catalogue(issue)
    pair, claims = base.public_contrast(issue), obligations(issue)
    anchors = []
    for row in catalog["spans"]:
        text = row["text"]
        if not row["quote_eligible"] or base.gate_role(text) in base.BAD_ROLES:
            continue
        kind = "explicit_interface_request" if any(row["start"] <= c["start"] < row["end"] for c in claims) else (
            "comparative_report" if pair and re.search(r"\b(?:works|succeeds)\s+(?:for|with)\s*$", text, re.I) else
            "regression_report" if re.search(r"(?:earlier|previous|used to|before|<=)", text, re.I)
                and re.search(r"\b(?:works?|worked|without raising)\b", text, re.I) else None
        )
        if kind:
            anchors.append({"quote_ref": row["id"], "kind": kind,
                "origin": "explicit_public_request" if kind == "explicit_interface_request" else "completion_hypothesis_from_public_report",
                "explicit_public_request": kind == "explicit_interface_request",
                "reported_promise_proven": False, "semantic_alignment_proven": False})
    return {"schema": "e1c2-public-report-anchors-v1", "issue_sha256": catalog["issue_sha256"], "anchors": anchors[:4],
            "public_API_pair": [c.func.attr for c in pair] if pair else None,
            "unknown_if_no_anchor": not anchors, "grammar_limited": True, "literal_expected_values_invented": False}


def revise_policy(text):
    for original in ("Missing desired behavior requires abstention.", "Unknown desired behavior still requires abstention.",
                     "Unknown EXPECTATION requires abstention;"):
        text = text.replace(original, "Unanchored expectation requires abstention; public comparative/regression anchors allow a labeled completion hypothesis.")
    return text


def messages(frozen, feedback=None, previous=None):
    value = _messages(frozen, feedback, previous)
    body = json.loads(value[1].content)
    body["public_report_anchors"] = report_anchors(frozen["issue"])
    audit_repair_visible_payload(body)
    text = input_json(body)
    if len(text) > 30000:
        raise ProviderBudgetExceeded("report anchor context exhausted before provider")
    value[1] = HumanMessage(content=text)
    value[0] = SystemMessage(content=revise_policy(value[0].content) + (
        " public_report_anchors are limited public-text classifications, not truth certificates. A comparative "
        "or regression report may support a call_completes HYPOTHESIS anchored to its exact prose quote_ref; "
        "do not require the literal word 'should', and do not use a traceback/code quote. Such completion is "
        "inferred, not an explicit original promise. For comparative reports actually exercise the recorded normal "
        "API and target API with the same own shared inputs; do not omit the problematic parameter. Unknown "
        "semantics remain unknown. Never invent literal expected values or claim a hypothesis is report-exact. "
        "Keep the original seven probe fields only; Controller records the origin, not an extra model field."
    ))
    return value


def conversation(msgs, turn, prior=None, observed=None):
    value = _conversation(msgs, turn, prior, observed)
    value[-1] = HumanMessage(content=revise_policy(value[-1].content))
    if sum(len(str(m.content)) for m in value) > 36000:
        raise ProviderBudgetExceeded("report anchor conversation exhausted before provider")
    return value


def execute_probe(payload, frozen, workspace, image, root, environment, locked=None):
    evidence = report_anchors(frozen["issue"])
    spans = catalogue(frozen["issue"])["spans"]
    matched = [a for a in evidence["anchors"] if spans[a["quote_ref"]]["text"] == payload["expected_quote"]]
    _save(root / "expectation-origin.json", {"matched_anchors": matched, "semantic_alignment_proven": False,
        "inferred_completion_not_literal_value": bool(matched and payload["oracle"] == "call_completes"),
        "controller_modified_probe": False})
    feedback, oracle, candidate, execution = _execute(payload, frozen, workspace, image, root, environment, locked)
    if feedback["status"] == "action_rejected":
        feedback = {**feedback, "public_report_anchors": evidence, "facts_not_removed_by_quote_rejection": True}
    return feedback, oracle, candidate, execution


def preflight():
    return {**_preflight(), "schema": "e1c2-report-anchor-four-reference-dev-v1",
            "inferred_report_completion_explicitly_labeled": True, "bad_quote_gate_unchanged": True,
            "unknown_not_automatically_trusted": True, "budget_changed": False}


@contextmanager
def configured():
    with ExitStack() as stack:
        for key, value in (("OUT", OUT), ("SMOKE", SMOKE), ("PROTOCOL", PROTOCOL), ("MODULES", MODULES),
                           ("messages", messages), ("preflight", preflight)):
            stack.enter_context(patch.object(base, key, value))
        stack.enter_context(_configured())
        stack.enter_context(patch.object(_compiled, "execute_probe", execute_probe))
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
