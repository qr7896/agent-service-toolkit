"""Strict typed-action interoperability, not an input-echo or schema bypass."""

from __future__ import annotations

import json

from evals.e1c_evaluation_2_bounded_repro_loop import parse_action as canonical_parse
from evals.e1c_evaluation_2_contract_method import CONTRACT_KEYS
from evals.e1c_evaluation_2_probe import input_json


def parse_action(raw):
    value = json.loads(raw)
    if isinstance(value, dict) and "type" in value:
        kind = value["type"]
        if kind in {"retrieve", "read", "abstain_reason"} and set(value) == {"type", kind}:
            value = {kind: value[kind]}
        elif kind == "probe" and set(value) == {"type", *CONTRACT_KEYS}:
            value = {"probe": {k: value[k] for k in CONTRACT_KEYS}}
        else:
            raise ValueError("typed_action_fields_mismatch")
    return canonical_parse(input_json(value))
