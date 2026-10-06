"""Controller-owned execution grammar, independent of model formatting metadata."""

from __future__ import annotations

import ast
import json
import re

from evals.e1c_evaluation_2_contract_method import parse_response as legacy_parse
from evals.e1c_evaluation_2_execution_contract import _reject_native_fixture_harness, prepare_source


def parse_response(raw, role):
    fenced = re.fullmatch(r"\s*```json\s*\n(.*?)\n```\s*", raw, re.S)
    value = json.loads(fenced.group(1) if fenced else raw)
    ignored = isinstance(value, dict) and "execution" in value
    if isinstance(value, dict):
        value = {key: item for key, item in value.items() if key != "execution"}
    parsed = legacy_parse(json.dumps(value), role)
    if parsed["status"] == "abstained":
        return parsed
    spec = {"mode": "direct_script", "entrypoint": None, "fixture_source": "generated_public_issue_only"}
    for key in (("source",) if role == "A" else ("setup_source", "control_action", "target_action", "assertion")):
        _reject_native_fixture_harness(parsed["payload"][key])
    if role == "A":
        source = parsed["payload"]["source"]
        tree = ast.parse(source)
        inert = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef)
        functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if functions and all(isinstance(node, inert) or isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                             and isinstance(node.value.value, str) for node in tree.body):
            spec = {**spec, "mode": "call_entrypoint", "entrypoint": functions[0].name}
        parsed["payload"]["source"] = prepare_source(source, spec)
    return {**parsed, "execution_spec": spec, "execution_owner": "controller_grammar",
            "model_execution_metadata_ignored": ignored}
