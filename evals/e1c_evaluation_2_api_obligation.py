"""Conservative public constructor-keyword obligations and fixture provenance.

One explicit prose grammar, not universal intent understanding. Unknown binding
is not a semantic certificate. Never edits code, values, quotes or an oracle.
"""

from __future__ import annotations

import ast
import re

from evals.e1c_evaluation_2_dev_pilot import _sha
from evals.e1c_evaluation_2_issue_fixture_facts import expression
from evals.e1c_evaluation_2_public_api_windows import resolve_method, resolve_symbol
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

REQUEST = re.compile(
    r"\b(?:expose|accept|support)\s+`(?P<parameter>[A-Za-z_]\w*)`\s+(?:in|on|via)\s+"
    r"`(?P<api>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\.__init__(?:\(\))?`", re.I,
)


def obligations(issue):
    audit_repair_visible_payload({"issue": issue})
    return [{"kind": "constructor_keyword_acceptance", "api": m["api"], "owner": m["api"].split(".")[-1],
             "parameter": m["parameter"], "public_quote": m[0], "start": m.start(), "end": m.end(),
             "grammar_limited": True} for m in REQUEST.finditer(issue)][:4]


def verify_entrypoint(payload, frozen, workspace):
    claims = obligations(frozen["issue"])
    program = ast.parse(payload["setup_source"] + "\n" + payload["target_action"])
    imports = {a.asname or a.name: (n.module, a.name) for n in program.body if isinstance(n, ast.ImportFrom)
               and n.module and n.level == 0 for a in n.names}
    writes = {n.id for n in ast.walk(program) if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del))}
    writes.update(n.name for n in ast.walk(program) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
    calls = []
    for statement in program.body:
        if not isinstance(statement, (ast.Assign, ast.Expr)):
            continue
        value = statement.value
        if any(isinstance(n, (ast.IfExp, ast.BoolOp, ast.Lambda, ast.ListComp, ast.GeneratorExp)) for n in ast.walk(value)):
            continue
        calls.extend(n for n in ast.walk(value) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name))
    rows = []
    for claim in claims:
        row = {**claim, "status": "unknown", "source_signature": None, "semantic_alignment_proven": False}
        aliases = [(alias, module, symbol) for alias, (module, symbol) in imports.items() if symbol == claim["owner"]]
        if len(aliases) != 1:
            rows.append(row)
            continue
        alias, module, symbol = aliases[0]
        public_prefix = claim["api"].rsplit(".", 1)[0] if "." in claim["api"] else None
        if public_prefix and not (module == public_prefix or module.startswith(public_prefix + ".")):
            rows.append({**row, "reason": "public_qualified_module_binding_unknown"})
            continue
        if alias in writes:
            rows.append({**row, "reason": "import_alias_shadowed"})
            continue
        record = resolve_symbol(workspace, module, symbol)
        method = resolve_method(workspace, record, "__init__") if record else None
        if not method:
            rows.append(row)
            continue
        args = method["node"].args
        names = [n.arg for n in (*args.args, *args.kwonlyargs)]
        row["source_signature"] = {"path": method["path"].relative_to(workspace).as_posix(),
                                   "line": method["node"].lineno, "source_sha256": _sha(method["path"]),
                                   "keyword_parameters": names, "has_var_kwargs": args.kwarg is not None,
                                   "requested_parameter_declared": claim["parameter"] in names}
        applicable = [call for call in calls if call.func.id == alias]
        if any(any(k.arg == claim["parameter"] for k in call.keywords) for call in applicable):
            row["status"] = "explicit_entrypoint_exercised_semantics_unverified"
        elif any(any(k.arg is None for k in call.keywords) for call in applicable):
            row["reason"] = "dynamic_keyword_mapping_unproven"
        else:
            row["status"] = "explicit_entrypoint_obligation_unfulfilled"
        rows.append(row)
    return {"schema": "e1c2-public-api-obligation-v1", "grammar_limited": True,
            "status": "not_applicable" if not claims else "fulfilled_syntactically" if all(
                r["status"] == "explicit_entrypoint_exercised_semantics_unverified" for r in rows
            ) else "unfulfilled_or_unknown", "rows": rows,
            "code_changed": False, "oracle_changed": False, "machine_trusted": False}


def argument_provenance(payload, frozen):
    setup = ast.parse(payload["setup_source"])
    writes = {}
    for n in ast.walk(setup):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            writes[n.id] = writes.get(n.id, 0) + 1
    bindings = {n.targets[0].id: n.value for n in setup.body if isinstance(n, ast.Assign)
                and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and writes[n.targets[0].id] == 1}
    public = {fact["name"]: fact["value"] for block in frozen.get("public_fixture_facts", [])
              for fact in block["facts"] if fact["kind"] == "fixture_binding"}
    rows = []
    for call in ast.walk(ast.parse(payload["target_action"])):
        if not isinstance(call, ast.Call):
            continue
        for keyword in call.keywords:
            node = keyword.value
            name = node.id if isinstance(node, ast.Name) else None
            value = bindings.get(name, node)
            try:
                value_fact = expression(value)
                exact = name in public and public[name] == value_fact
            except ValueError:
                exact = False
            tag = type(value).__name__ if isinstance(value, (ast.List, ast.Tuple, ast.Dict, ast.Constant)) else "unknown_without_runtime_observation"
            rows.append({"parameter": keyword.arg, "variable": name, "static_form": tag,
                         "provenance": "public_binding_exact_match" if exact else "model_fixture_hypothesis_or_unknown",
                         "public_expression_exact_match": exact,
                         "reported_input_type_proven": False, "runtime_type_observed": False})
    return {"schema": "e1c2-probe-argument-provenance-v1", "rows": rows,
            "values_changed": False, "hypotheses_are_not_reported_facts": True}
