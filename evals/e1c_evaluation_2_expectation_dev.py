"""OLD DEV: reject trace expectations and bind explicit public API contrasts."""

from __future__ import annotations

import argparse
import ast
import asyncio
import re
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from langchain_core.messages import SystemMessage

from evals import e1c_evaluation_2_execution_plan_dev_v2 as base
from evals.e1c_evaluation_2_contract_recovery import tree_sha
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_guard_evidence_audit import guard_evidence
from evals.e1c_evaluation_2_issue_quote_refs import catalogue
from evals.e1c_evaluation_2_probe import input_json
from evals.e1c_evaluation_2_public_api_windows import resolve_symbol
from evals.e1c_evaluation_2_witness_grounding_audit import audit, expectation_role

OUT = ROOT / ".codex/e1c/evaluation_2/expectation-reference-dev-v1"
SMOKE = ROOT / ".codex/e1c/evaluation_2/expectation-zero-smoke-v1"
PROTOCOL = ROOT / "docs/research/E1C2_EXPECTATION_DEV_V1_PROTOCOL_2026-10-07.md"
MODULES = (*base.MODULES, "evals/e1c_evaluation_2_witness_grounding_audit.py", "evals/e1c_evaluation_2_expectation_dev.py")
_compiled = base.base._compiled
_configured, _preflight, _execute, _messages = base.configured, base.preflight, base.base.execute_probe, base.base.base.messages
BAD_ROLES = {"runtime_trace_not_desired_behavior", "code_or_literal_not_desired_behavior", "empty"}


def gate_role(quote):
    if re.search(r'^\s*(?:File ["\'].*?, line \d+|Traceback(?:\s*\(|:|$)|[\w.]+(?:Error|Exception):)', quote, re.M):
        return "runtime_trace_not_desired_behavior"
    if re.search(r"^\s*(?:if|elif|while|for)\s+.+:\s*$", quote, re.M):
        return "code_or_literal_not_desired_behavior"
    return expectation_role(quote)


def public_contrast(issue):
    """One explicit works-for / but-not-for pair; unknown syntax stays unknown."""
    lines = issue.splitlines()
    starts = [i for i, text in enumerate(lines) if re.search(r"\b(?:works|succeeds)\s+(?:for|with)\s*$", text, re.I)]
    splits = [i for i, text in enumerate(lines) if re.fullmatch(r"\s*but\s+not\s+(?:for|with)\s*", text, re.I)]
    if len(starts) != 1 or len(splits) != 1 or starts[0] >= splits[0]:
        return None

    def calls(block):
        found = []
        for text in block:
            try:
                tree = ast.parse(text.strip())
            except SyntaxError:
                continue
            if len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Call):
                call = tree.body[0].value
                if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and all(k.arg for k in call.keywords):
                    found.append(call)
        return found

    normal, target = calls(lines[starts[0] + 1:splits[0]]), calls(lines[splits[0] + 1:])
    if len(normal) != 1 or len(target) != 1 or normal[0].func.attr == target[0].func.attr:
        return None
    return normal[0], target[0]


def contrast_binding(payload, frozen, workspace):
    pair = public_contrast(frozen["issue"])
    result = {"schema": "e1c2-public-api-contrast-binding-v1", "status": "not_applicable" if pair is None else "unfulfilled_or_unknown",
              "grammar_limited": True, "semantic_alignment_proven": False, "source_bindings": [],
              "actual_shared_values_proven": False, "public_alias_scope_proven": False}
    if pair is None:
        return result
    result["public_terminal_APIs"] = [c.func.attr for c in pair]
    setup = ast.parse(payload["setup_source"])
    imports = {a.asname or a.name: (n.module, a.name) for n in setup.body if isinstance(n, ast.ImportFrom)
               and n.module and not n.level for a in n.names}
    writes = {n.id for n in ast.walk(setup) if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del))}
    writes.update(n.name for n in ast.walk(setup) if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)))
    hashes = {r["path"]: r["source_sha256"] for r in frozen["windows"]}
    own = []
    for field, public in zip(("control_action", "target_action"), pair, strict=True):
        tree = ast.parse(payload[field])
        if len(tree.body) != 1 or not isinstance(tree.body[0], (ast.Expr, ast.Assign)) or not isinstance(tree.body[0].value, ast.Call):
            return result
        call = tree.body[0].value
        if not isinstance(call.func, ast.Name) or call.func.id not in imports or call.func.id in writes:
            return result
        module, symbol = imports[call.func.id]
        record = resolve_symbol(workspace, module, symbol) if symbol == public.func.attr else None
        if not record or not isinstance(record["node"], ast.FunctionDef):
            return result
        path = record["path"].relative_to(workspace).as_posix()
        if path not in hashes or _sha(record["path"]) != hashes[path]:
            raise ValueError("contrast source not in unchanged exposed production")
        result["source_bindings"].append({"path": path, "line": record["node"].lineno, "symbol": symbol, "source_sha256": hashes[path]})
        own.append(call)
    public_keywords = [{k.arg: k.value for k in c.keywords} for c in pair]
    shared = sorted(set(public_keywords[0]) & set(public_keywords[1]))
    if not shared or any(k.arg is None for c in own for k in c.keywords) or len(pair[0].args) != len(pair[1].args):
        return result
    own_keywords = [{k.arg: k.value for k in c.keywords} for c in own]
    for key in shared:
        a, b = public_keywords[0][key], public_keywords[1][key]
        if tree_sha(a) != tree_sha(b) or any(key not in mapping for mapping in own_keywords):
            return result
        actual = [mapping[key] for mapping in own_keywords]
        if any(not isinstance(n, (ast.Name, ast.Constant)) for n in actual) or tree_sha(actual[0]) != tree_sha(actual[1]):
            return result
        if isinstance(a, ast.Constant) and tree_sha(a) != tree_sha(actual[0]):
            return result
    if len(own[0].args) != len(pair[0].args) or len(own[1].args) != len(pair[1].args):
        return result
    if any(tree_sha(a) != tree_sha(b) or not isinstance(a, (ast.Name, ast.Constant))
           for a, b in zip(own[0].args, own[1].args, strict=True)):
        return result
    for a, b, actual in zip(pair[0].args, pair[1].args, own[0].args, strict=True):
        if tree_sha(a) != tree_sha(b) or isinstance(a, ast.Constant) and tree_sha(a) != tree_sha(actual):
            return result
    result.update({"status": "explicit_contrast_exercised_syntactically", "shared_keywords": shared})
    return result


def execute_probe(payload, frozen, workspace, image, root, environment, locked=None):
    oracle = {k: payload[k] for k in ("issue_quote", "expected_quote", "oracle", "assertion")}
    if locked is not None and oracle != locked:
        raise ValueError("oracle_changed_after_feedback")
    if any(not 8 <= len(payload[k]) <= 1500 or payload[k] not in frozen["issue"] for k in ("issue_quote", "expected_quote")):
        raise ValueError("contract_quote_not_in_allowed_issue")
    role = gate_role(payload["expected_quote"])
    binding = contrast_binding(payload, frozen, workspace) if role not in BAD_ROLES else None
    _save(root / "expectation-binding.json", {"role": role, "contrast": binding, "semantic_alignment_proven": False})
    if role in BAD_ROLES or binding["status"] == "unfulfilled_or_unknown":
        return {"status": "action_rejected", "reason": "public_expectation_or_contrast_requires_revision",
                "expectation_role": role, "contrast": binding, "oracle_not_locked": locked is None,
                "prose_quote_ids_not_semantic_certificates": [r["id"] for r in catalogue(frozen["issue"])["spans"]
                    if r["quote_eligible"] and gate_role(r["text"]) not in BAD_ROLES][:8]}, locked, None, None
    feedback, oracle, candidate, execution = _execute(payload, frozen, workspace, image, root, environment, locked)
    if execution is not None:
        sites = [r for r in guard_evidence(payload, frozen, workspace)["rows"] if r["matches_public_failure_condition"]]
        grounding = audit(payload, sites, execution)
        grounding["reported_API_contrast_exercised_syntactically"] = binding["status"] == "explicit_contrast_exercised_syntactically"
        _save(root / "witness-grounding.json", grounding)
    return feedback, oracle, candidate, execution


def messages(frozen, feedback=None, previous=None):
    value = _messages(frozen, feedback, previous)
    value[0] = SystemMessage(content=value[0].content + (
        " Expectation gate runs BEFORE oracle lock: traceback/source-code/data quotes cannot establish desired behavior. "
        "Use an exact public prose reference; unknown prose is not automatically certified. Where the public report "
        "explicitly contrasts working API A with failing API B, the normal control must exercise A and the target B "
        "with identical own shared argument expressions and preserved public literal constraints. Do not omit the "
        "problem parameter from the normal control. Retrieve the production API if needed; never invent an expectation."
    ))
    return value


def preflight():
    return {**_preflight(), "schema": "e1c2-expectation-contrast-four-reference-dev-v1",
            "negative_expectation_role_gate_before_lock": True, "limited_public_contrast_binding": True,
            "semantic_trust_not_automatically_promoted": True, "budget_changed": False}


@contextmanager
def configured():
    with ExitStack() as stack:
        for key, value in (("OUT", OUT), ("SMOKE", SMOKE), ("PROTOCOL", PROTOCOL), ("MODULES", MODULES), ("preflight", preflight)):
            stack.enter_context(patch.object(base, key, value))
        stack.enter_context(patch.object(base.base.base, "messages", messages))
        stack.enter_context(_configured())
        stack.enter_context(patch.object(_compiled, "execute_probe", execute_probe))
        stack.enter_context(patch.object(_compiled.base.loop, "execute_probe", execute_probe))
        yield


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "preflight", "run", "gold"))
    args = parser.parse_args()
    with configured():
        value = asyncio.run(_compiled.smoke()) if args.command == "smoke" else _compiled.freeze() if args.command == "preflight" else asyncio.run(_compiled.run()) if args.command == "run" else _compiled.grade()
    print(input_json(value), flush=True)
