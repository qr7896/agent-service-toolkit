"""Explicit, bounded generated-probe entrypoints; no implicit fixture hydration."""

from __future__ import annotations

import ast
import json
import re

from evals.e1c_evaluation_2_contract_method import parse_response as legacy_parse
from evals.e1c_evaluation_2_import_seed_audit import invocation_status

FIELDS = {"mode", "entrypoint", "fixture_source"}


class ExecutionContractViolation(ValueError):
    pass


def _reject_native_fixture_harness(source):
    """This protocol has no trusted generated-file/native-runner adapter yet."""
    tree = ast.parse(source)
    imported = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update({alias.asname or alias.name: alias.name for alias in node.names})
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            imported.update({alias.asname or alias.name: node.module + "." + alias.name for alias in node.names})
    def name(node):
        if isinstance(node, ast.Name):
            return imported.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            parent = name(node.value)
            return parent + "." + node.attr if parent else ""
        return ""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None and name(node.value) in {"pytest", "_pytest.config"}:
            raise ExecutionContractViolation("native_module_alias_fixture_provenance_not_supported")
        if not isinstance(node, (ast.Call, ast.Attribute, ast.Name)):
            continue
        resolved = name(node.func) if isinstance(node, ast.Call) else name(node)
        if (resolved in {"pytest.main", "_pytest.config.main"}
                or resolved.rsplit(".", 1)[-1] in {"runpytest", "runpytest_subprocess", "makepyfile", "makeconftest"}):
            raise ExecutionContractViolation("native_test_harness_fixture_provenance_not_supported")


def _check_spec(spec, role):
    if not isinstance(spec, dict) or set(spec) != FIELDS or spec["fixture_source"] != "generated_public_issue_only":
        raise ExecutionContractViolation("execution_manifest_missing_or_untrusted_fixture")
    if spec["mode"] == "direct_script" and spec["entrypoint"] is None:
        return
    if role != "A" or spec["mode"] != "call_entrypoint" or not isinstance(spec["entrypoint"], str):
        raise ExecutionContractViolation("unsupported_execution_mode")
    if not re.fullmatch(r"[A-Za-z]\w*", spec["entrypoint"]):
        raise ExecutionContractViolation("entrypoint_must_be_plain_local_identifier")


def prepare_source(source, spec):
    _check_spec(spec, "A")
    tree = ast.parse(source)
    if spec["mode"] == "direct_script":
        if invocation_status(source) == "function_bodies_not_invoked_by_direct_script":
            raise ExecutionContractViolation("function_body_not_invoked")
        return source
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    if len(functions) != 1 or functions[0].name != spec["entrypoint"]:
        raise ExecutionContractViolation("entrypoint_missing_ambiguous_or_async")
    function = functions[0]
    if (function.decorator_list or function.returns or getattr(function, "type_params", [])
            or function.args.posonlyargs or function.args.args or function.args.kwonlyargs
            or function.args.vararg or function.args.kwarg):
        raise ExecutionContractViolation("entrypoint_requires_parameters_or_definition_side_effects")
    if any(not isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)) and not (
            isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str))
           for node in tree.body):
        raise ExecutionContractViolation("call_entrypoint_requires_inert_module_top_level")
    if any(isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id == function.name
           for node in ast.walk(function)):
        raise ExecutionContractViolation("entrypoint_binding_reassigned")
    if not any(isinstance(node, ast.Assert) for node in ast.walk(function)):
        raise ExecutionContractViolation("entrypoint_has_no_generated_behavior_check")
    return source.rstrip() + f"\n\n{function.name}()\n"


def parse_response(raw, role):
    fenced = re.fullmatch(r"\s*```json\s*\n(.*?)\n```\s*", raw, re.S)
    value = json.loads(fenced.group(1) if fenced else raw)
    if not isinstance(value, dict):
        raise ExecutionContractViolation("response_not_object")
    if set(value) == {"abstain_reason"}:
        return legacy_parse(raw, role)
    spec = value.get("execution")
    _check_spec(spec, role)
    parsed = legacy_parse(json.dumps({key: item for key, item in value.items() if key != "execution"}), role)
    for key in (("source",) if role == "A" else ("setup_source", "control_action", "target_action", "assertion")):
        _reject_native_fixture_harness(parsed["payload"][key])
    if role == "A":
        parsed["payload"]["source"] = prepare_source(parsed["payload"]["source"], spec)
    return {**parsed, "execution_spec": spec}
