"""Separate OLD DEV trial: exact typed/ref DTO compatibility, no field guessing."""

from __future__ import annotations

import argparse
import asyncio
import json
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from langchain_core.messages import SystemMessage

from evals import e1c_evaluation_2_unified_policy_dev as base
from evals.e1c_evaluation_2_dev_pilot import ROOT
from evals.e1c_evaluation_2_issue_quote_refs import REF_KEYS
from evals.e1c_evaluation_2_probe import input_json

OUT = ROOT / ".codex/e1c/evaluation_2/unified-codec-reference-dev-v1"
SMOKE = ROOT / ".codex/e1c/evaluation_2/unified-codec-zero-smoke-v1"
PROTOCOL = ROOT / "docs/research/E1C2_UNIFIED_CODEC_DEV_V1_PROTOCOL_2026-10-07.md"
MODULES = (*base.MODULES, "evals/e1c_evaluation_2_unified_codec_dev.py")
_configured, _messages, _preflight, _decode = base.configured, base.messages, base.preflight, base._ready.decode
EXAMPLE = input_json({"probe": {"issue_quote_ref": 0, "expected_quote_ref": 1, "oracle": "call_completes",
                              "setup_source": "<production imports and fixture>", "control_action": "<supported normal API call>",
                              "target_action": "<target API call>", "assertion": ""}})


def decode(raw, issue):
    value = json.loads(raw)
    if isinstance(value, dict):
        fields = set(value)
        if fields == {"type", *REF_KEYS} and value["type"] == "probe":
            value = {"probe": {k: value[k] for k in REF_KEYS}}
        elif fields == {"action", *REF_KEYS} and value["action"] == "probe":
            value = {"probe": {k: value[k] for k in REF_KEYS}}
        elif fields == {"type", "action", *REF_KEYS} and value["type"] == "json_object" and value["action"] == "probe":
            value = {"probe": {k: value[k] for k in REF_KEYS}}
    action, payload, proof = _decode(input_json(value), issue)
    return action, payload, {**proof, "known_typed_ref_shape_only": True}


def messages(frozen, feedback=None, previous=None):
    value = _messages(frozen, feedback, previous)
    value[0] = SystemMessage(content=value[0].content + (
        " Canonical JSON shape example (angle-bracket contents are placeholders, NOT executable code): " + EXAMPLE +
        ' Return one outer key only. Other shapes: {"retrieve":"Class.method"}, '
        '{"read":{"path":"already exposed path","start_line":1}}, {"abstain_reason":"reason"}. '
        "Fill real code from production APIs; do not copy placeholders."
    ))
    return value


def preflight():
    return {**_preflight(), "schema": "e1c2-unified-codec-four-reference-dev-v1",
            "exact_typed_reference_variants_supported": True, "canonical_JSON_example": True}


@contextmanager
def configured():
    with ExitStack() as stack:
        for key, value in (("OUT", OUT), ("SMOKE", SMOKE), ("PROTOCOL", PROTOCOL), ("MODULES", MODULES),
                           ("messages", messages), ("preflight", preflight)):
            stack.enter_context(patch.object(base, key, value))
        stack.enter_context(patch.object(base._ready, "decode", decode))
        stack.enter_context(_configured())
        yield


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "preflight", "run", "gold"))
    args = parser.parse_args()
    with configured():
        value = asyncio.run(base._compiled.smoke()) if args.command == "smoke" else base._compiled.freeze() if args.command == "preflight" else asyncio.run(base._compiled.run()) if args.command == "run" else base._compiled.grade()
    print(input_json(value), flush=True)
