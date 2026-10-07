"""Derive one normal datetime-format control from verified production strptime.

Only the control changes. No task names, date literals, manual source paths,
expected-value edits, Gold inputs or equivalence claims are used here.
"""

from __future__ import annotations

import ast
from datetime import datetime

from evals.e1c_evaluation_2_source_contract import source_trees


def derive_format_control(payload, frozen, workspace):
    proof = {"schema": "e1c2-source-format-control-v1", "compiled": False,
             "target_changed": False, "oracle_changed": False, "semantic_equivalence_proven": False,
             "target_format_binding_proven": False}
    if payload["oracle"] != "call_completes":
        return dict(payload), proof
    target = ast.parse(payload["target_action"])
    setup = ast.parse(payload["setup_source"])
    if len(target.body) != 1 or not isinstance(target.body[0], (ast.Expr, ast.Assign)) or not isinstance(target.body[0].value, ast.Call):
        return dict(payload), proof
    if any(isinstance(n, (ast.Global, ast.Nonlocal, ast.NamedExpr)) or (
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        and n.func.id in {"globals", "locals", "vars", "setattr", "eval", "exec"}
    ) for n in ast.walk(setup)):
        return dict(payload), proof
    writes = {}
    for node in ast.walk(setup):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            writes[node.id] = writes.get(node.id, 0) + 1
    bindings = {n.targets[0].id: n.value for n in setup.body if isinstance(n, ast.Assign) and len(n.targets) == 1
                and isinstance(n.targets[0], ast.Name) and writes[n.targets[0].id] == 1
                and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)}
    call = target.body[0].value
    values = []
    for argument in [*call.args, *(k.value for k in call.keywords)]:
        if any(isinstance(n, ast.Call) for n in ast.walk(argument)):
            continue
        for node in ast.walk(argument):
            literal = bindings.get(node.id) if isinstance(node, ast.Name) else node
            if not isinstance(literal, ast.Constant) or not isinstance(literal.value, str) or len(literal.value) > 100:
                continue
            try:
                parsed = datetime.fromisoformat(literal.value)
            except ValueError:
                continue
            values.append((node, literal.value, parsed))
    if len(values) != 1:
        return dict(payload), proof
    formats = []
    for path, tree in source_trees(frozen, workspace):
        aliases = {a.asname or a.name: a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        aliases.update({a.asname or a.name: n.module + "." + a.name for n in ast.walk(tree)
                        if isinstance(n, ast.ImportFrom) and n.module == "datetime" for a in n.names})

        def qualified(node):
            if isinstance(node, ast.Name):
                return aliases.get(node.id, node.id)
            return qualified(node.value) + "." + node.attr if isinstance(node, ast.Attribute) else ""

        shadowed = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del))}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or len(node.args) != 2 or node.keywords:
                continue
            root = node.func
            while isinstance(root, ast.Attribute):
                root = root.value
            if not isinstance(root, ast.Name) or root.id in shadowed or qualified(node.func) != "datetime.datetime.strptime":
                continue
            fmt = node.args[1]
            if isinstance(fmt, ast.Constant) and isinstance(fmt.value, str) and len(fmt.value) <= 100 and all(
                directive in fmt.value for directive in ("%Y", "%m", "%d", "%H", "%M", "%S")
            ):
                formats.append((path, node.lineno, fmt.value))
    for path, line, fmt in sorted(formats):
        try:
            normal = values[0][2].strftime(fmt)
        except (ValueError, OverflowError):
            continue
        if normal == values[0][1]:
            continue

        class Replace(ast.NodeTransformer):
            def visit(self, node):
                return ast.Constant(value=normal) if node is values[0][0] else super().visit(node)

        control = ast.unparse(ast.fix_missing_locations(Replace().visit(target)))
        result = {**payload, "control_action": control}
        if any(result[k] != payload[k] for k in payload if k != "control_action"):
            raise ValueError("source format compiler changed target or oracle")
        proof.update({"compiled": True, "source_path": path, "source_line": line, "source_format": fmt,
                      "normal_control_requires_two_base_passes": True, "original_control_replaced": True,
                      "timezone_or_representation_may_differ": True})
        return result, proof
    return dict(payload), proof
