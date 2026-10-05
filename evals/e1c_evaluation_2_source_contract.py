"""Next-DEV source contracts: environment imports and target-construction frontier."""

from __future__ import annotations

import ast

from evals.e1c_evaluation_2_contract_method import build_pair
from evals.e1c_evaluation_2_dev_pilot import _sha
from evals.e1c_evaluation_2_probe import issue_missing_optional_import
from evals.e1c_strict_v5_boundary import assert_production_relative_path


def source_trees(frozen, workspace):
    hashes = {row["path"]: row["source_sha256"] for row in frozen["windows"]}
    for name in sorted(set(frozen["candidate_paths"])):
        assert_production_relative_path(name)
        path = workspace / name
        if path.is_symlink() or not path.resolve().is_relative_to(workspace.resolve()) or _sha(path) != hashes[name]:
            raise ValueError("production source changed before source-contract analysis")
        yield name, ast.parse(path.read_text(encoding="utf-8", errors="replace"))


def optional_import(frozen, workspace):
    imports, evidence = set(), []
    for path, tree in source_trees(frozen, workspace):
        for node in ast.walk(tree):
            names = [item.name.split(".")[0] for item in node.names] if isinstance(node, ast.Import) else (
                [node.module.split(".")[0]] if isinstance(node, ast.ImportFrom) and node.module else []
            )
            for name in names:
                imports.add(name)
                evidence.append({"path": path, "line": node.lineno, "module": name})
    enriched = {**frozen, "windows": [{"text": "\n".join(f"import {name}" for name in sorted(imports))}]}
    module = issue_missing_optional_import(enriched)
    return {"missing_optional_import": module, "evidence": [row for row in evidence if row["module"] == module]}


def rephase_setup(payload, frozen, workspace):
    """Move source-proven unsupported keyword construction into the target phase."""
    source = payload["setup_source"]
    setup = ast.parse(source)
    imported = {alias.asname or alias.name: alias.name for node in setup.body if isinstance(node, ast.ImportFrom)
                for alias in node.names}
    signatures = {}
    for _, tree in source_trees(frozen, workspace):
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                ctors = [child for child in node.body if isinstance(child, ast.FunctionDef) and child.name == "__init__"]
                if len(ctors) == 1 and ctors[0].args.kwarg is None:
                    args = ctors[0].args
                    names = {item.arg for item in [*args.posonlyargs, *args.args, *args.kwonlyargs]}
                    signatures.setdefault(node.name, []).append(names)
    for statement in setup.body:
        if not isinstance(statement, ast.Assign) or not isinstance(statement.value, ast.Call):
            continue
        call = statement.value
        if not isinstance(call.func, ast.Name) or call.func.id not in imported:
            continue
        candidates = signatures.get(imported[call.func.id], [])
        if len(candidates) != 1:
            continue
        unsupported = sorted({item.arg for item in call.keywords if item.arg and item.arg not in candidates[0]})
        if unsupported:
            lines = source.splitlines()
            updated = {**payload, "setup_source": "\n".join(lines[:statement.lineno - 1]),
                       "target_action": "\n".join(lines[statement.lineno - 1:]) + "\n" + payload["target_action"]}
            before = ast.dump(ast.parse(payload["setup_source"] + "\n" + payload["target_action"]))
            after = ast.dump(ast.parse(updated["setup_source"] + "\n" + updated["target_action"]))
            if before != after:
                raise ValueError("construction-frontier shift changed the target program")
            return updated, {"moved_from_line": statement.lineno, "callee": imported[call.func.id],
                             "source_proven_unsupported_keywords": unsupported, "expected_relation_changed": False}
    return payload, {"moved_from_line": None, "expected_relation_changed": False}


def build_source_pair(payload, frozen, workspace):
    corrected, frontier = rephase_setup(payload, frozen, workspace)
    control, target = build_pair(corrected, frozen, workspace)
    return control, target, frontier
