"""Zero-call production guard coverage, seeded by public API/failed conditions.

Audit only: neither edits a probe nor certifies semantic alignment. No task IDs,
hand-picked production paths, test assertions, Gold inputs or provider calls.
"""

from __future__ import annotations

import ast
import re

from evals.e1c_evaluation_2_bounded_repro_loop import window
from evals.e1c_evaluation_2_source_contract import source_trees


def guard_evidence(payload, frozen, workspace):
    setup = ast.parse(payload["setup_source"])
    imported = {a.asname or a.name: a.name for n in setup.body if isinstance(n, ast.ImportFrom) for a in n.names}
    roots = {n.func.id for n in ast.walk(ast.parse(payload["target_action"])) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    seeds = {(None, imported[n]) for n in roots if n in imported}
    seeds.update(re.findall(r"`([A-Za-z_]\w*)\.([A-Za-z_]\w*)(?:\(\))?`", payload["issue_quote"]))
    conditions = set()
    for text in re.findall(r"^\s*if\s+(.+):\s*$", frozen["issue"], re.M):
        try:
            conditions.add(ast.dump(ast.parse(text, mode="eval").body, include_attributes=False))
        except SyntaxError:
            continue
    rows = []
    for path, tree in source_trees(frozen, workspace):
        owners = {id(child): parent.name for parent in ast.walk(tree) if isinstance(parent, ast.ClassDef)
                  for child in parent.body if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            matched = sorted((owner or "", name) for owner, name in seeds if name == function.name and (owner is None or owners.get(id(function)) == owner))
            if not matched:
                continue
            pending = [(function, 0)]
            while pending:
                node, depth = pending.pop()
                pending.extend((child, depth + 1) for child in ast.iter_child_nodes(node))
                if not isinstance(node, ast.If):
                    continue
                predicate = ast.unparse(node.test)
                is_failure_condition = ast.dump(node.test, include_attributes=False) in conditions
                visible = any(r["path"] == path and r.get("start_line", 1) <= node.lineno <= r.get("end_line", 0)
                              and predicate in r.get("text", "") for r in frozen["windows"])
                evidence = window(path, workspace, max(1, node.lineno - 4), symbol=function.name)
                rows.append({"path": path, "line": node.lineno, "predicate": predicate,
                             "source_sha256": evidence["source_sha256"], "relation_type": "guard",
                             "depth": depth, "origin": "public_api_or_failure_condition", "seed": matched,
                             "matches_public_failure_condition": is_failure_condition,
                             "already_visible": visible, "window": evidence,
                             "API_binding_or_semantics_proven": False})
    rows.sort(key=lambda r: (not r["matches_public_failure_condition"], r["path"], r["line"]))
    return {"schema": "e1c2-production-guard-coverage-v1", "provider_calls": 0,
            "live_integrated": False, "semantic_alignment_proven": False, "rows": rows}
