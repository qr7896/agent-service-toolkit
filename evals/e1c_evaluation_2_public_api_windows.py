"""Resolve public imports and terminal API calls without executing repository code."""

from __future__ import annotations

import ast
import re

from evals.e1c_blind_boundary import BlindBoundaryViolation
from evals.e1c_evaluation_2_dev_pilot import _sha
from evals.e1c_evaluation_2_production_coverage import production_path
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload


def resolve_symbol(workspace, module, symbol, depth=0, seen=frozenset()):
    if depth > 4 or (module, symbol) in seen or not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", module):
        return None
    found = []
    relative_module = module.replace(".", "/")
    for prefix in ("", "src/"):
        for suffix in (".py", "/__init__.py"):
            path = workspace / (prefix + relative_module + suffix)
            relative = path.relative_to(workspace).as_posix()
            try:
                if (path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(workspace.resolve())
                        and path.stat().st_size <= 1_000_000 and production_path(relative)):
                    found.append(path)
            except BlindBoundaryViolation:
                continue
    if len(found) != 1:
        return None
    path = found[0]
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return None
    direct = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol]
    if len(direct) == 1:
        return {"path": path, "module": module, "symbol": symbol, "node": direct[0], "depth": depth}
    matches = []
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        for alias in node.names:
            if (alias.asname or alias.name) != symbol:
                continue
            parts = module.split(".") if path.name == "__init__.py" else module.split(".")[:-1]
            if node.level:
                if node.level > len(parts) + 1:
                    continue
                target = ".".join(parts[:len(parts) - node.level + 1] + (node.module.split(".") if node.module else []))
            else:
                target = node.module or ""
            resolved = resolve_symbol(workspace, target, alias.name, depth + 1, seen | {(module, symbol)})
            if resolved:
                matches.append(resolved)
    return matches[0] if len(matches) == 1 else None


def resolve_method(workspace, record, method, depth=0):
    if depth > 2 or not isinstance(record["node"], ast.ClassDef):
        return None
    own = [node for node in record["node"].body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == method]
    if len(own) == 1:
        return {**record, "node": own[0], "symbol": method, "owner": record["symbol"], "inheritance_depth": depth}
    matches = []
    for base in record["node"].bases:
        if isinstance(base, ast.Name):
            parent = resolve_symbol(workspace, record["module"], base.id)
            if parent:
                parent = {**parent, "depth": parent["depth"] + record["depth"]}
            candidate = resolve_method(workspace, parent, method, depth + 1) if parent else None
            if candidate:
                matches.append(candidate)
    return matches[0] if len(matches) == 1 else None


def constructor(value):
    if value.get("kind") != "call":
        return None
    callee = value["callee"]
    if callee["kind"] == "reference":
        return callee["name"]
    return constructor(callee["owner"]) if callee["kind"] == "attribute" else None


def window(record, workspace):
    node, path = record["node"], record["path"]
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    first = node.body[0] if node.body else None
    doc = isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str)
    body_start = first.end_lineno + 1 if doc else first.lineno if first else node.lineno + 1
    signature_end = (first.lineno - 1) if first else node.lineno
    end = min(node.end_lineno, body_start + 40)
    slices = [{"start_line": node.lineno, "end_line": signature_end}, {"start_line": body_start, "end_line": end}]
    slices = [row for row in slices if row["start_line"] <= row["end_line"]]
    end = max(row["end_line"] for row in slices)
    text = "\n".join("\n".join(lines[row["start_line"] - 1:row["end_line"]]) for row in slices)[:2500]
    value = {"path": path.relative_to(workspace).as_posix(), "symbol": record["symbol"], "owner": record.get("owner"),
             "start_line": node.lineno, "end_line": end, "source_slices": slices, "text": text,
             "source_sha256": _sha(path), "origin": "public_import_terminal_api",
             "relation_type": "definition" if not record.get("inheritance_depth") else "inherited_method",
             "depth": record["depth"] + record.get("inheritance_depth", 0)}
    audit_repair_visible_payload(value)
    return value


def terminal_windows(facts, workspace):
    output = []
    for block in facts["blocks"]:
        imports, bindings = {}, {}
        for fact in block["facts"]:
            if fact["kind"] == "import" and fact["module"] and not fact.get("relative_level", 0):
                for alias in fact["names"]:
                    imports[alias["alias"] or alias["name"]] = (fact["module"], alias["name"])
            if fact["kind"] == "fixture_binding":
                bindings[fact["name"]] = constructor(fact["value"])
        call = block["terminal_call"]
        if not call or call["kind"] != "call":
            continue
        callee = call["callee"]
        symbol = callee.get("name") if callee["kind"] == "reference" else None
        if symbol in imports:
            seed = {"module": imports[symbol][0], "symbol": imports[symbol][1]}
            record = resolve_symbol(workspace, *imports[symbol])
        elif callee["kind"] == "attribute":
            owner = callee["owner"]
            owner_name = bindings.get(owner.get("name")) if owner["kind"] == "reference" else constructor(owner)
            seed = {"module": imports[owner_name][0], "symbol": imports[owner_name][1]} if owner_name in imports else None
            record = resolve_symbol(workspace, *imports[owner_name]) if owner_name in imports else None
            record = resolve_method(workspace, record, callee["name"]) if record else None
        else:
            record = None
        if record and isinstance(record["node"], (ast.FunctionDef, ast.AsyncFunctionDef)):
            item = window(record, workspace)
            item["origin_seed"] = seed
            if not any((row["path"], row["symbol"], row.get("owner")) == (item["path"], item["symbol"], item.get("owner")) for row in output):
                output.append(item)
    return output[:2]
