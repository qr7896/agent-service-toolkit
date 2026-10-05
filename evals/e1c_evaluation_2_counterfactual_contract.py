"""Conservative literal-container contrast; never execute code to infer values."""

from __future__ import annotations

import ast
import hashlib

from evals.e1c_evaluation_2_source_contract import source_trees


def _fingerprint(node):
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()


def _last_call(source):
    tree = ast.parse(source)
    final = tree.body[-1] if tree.body else None
    value = final.value if isinstance(final, (ast.Expr, ast.Assign)) else None
    return tree, value if isinstance(value, ast.Call) else None


def _aliases(setup):
    aliases, assigned = set(), set()
    for node in ast.walk(setup):
        if isinstance(node, ast.Import):
            aliases.update((alias.asname or alias.name) + ".array" for alias in node.names if alias.name == "numpy")
        elif isinstance(node, ast.ImportFrom) and node.module == "numpy":
            aliases.update(alias.asname or alias.name for alias in node.names if alias.name == "array")
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            assigned.add(node.id)
        if isinstance(node, (ast.Attribute, ast.Subscript)) and isinstance(node.ctx, ast.Store):
            root = node.value
            while isinstance(root, (ast.Attribute, ast.Subscript)):
                root = root.value
            if isinstance(root, ast.Name):
                assigned.add(root.id)
    return {name for name in aliases if name.split(".")[0] not in assigned}


def _sequence(node, bindings, aliases, seen=frozenset()):
    if isinstance(node, ast.Name) and node.id in bindings and node.id not in seen:
        return _sequence(bindings[node.id], bindings, aliases, seen | {node.id})
    if isinstance(node, (ast.List, ast.Tuple)):
        try:
            ast.literal_eval(node)
        except (ValueError, TypeError):
            return None
        return type(node).__name__, ast.List(elts=node.elts, ctx=ast.Load())
    if (isinstance(node, ast.Call) and ast.unparse(node.func) in aliases
            and len(node.args) == 1 and not node.keywords):
        inner = _sequence(node.args[0], bindings, aliases, seen)
        return ("numpy_array", inner[1]) if inner else None
    return None


def compile_pair(payload, frozen, workspace):
    """Derive a list control from an array target, preserving literal values only."""
    setup = ast.parse(payload["setup_source"])
    writes = {}
    for node in ast.walk(setup):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            writes[node.id] = writes.get(node.id, 0) + 1
        if isinstance(node, (ast.Attribute, ast.Subscript)) and isinstance(node.ctx, ast.Store) and isinstance(node.value, ast.Name):
            writes[node.value.id] = 2
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                writes[node.func.value.id] = 2
            for argument in [*node.args, *(keyword.value for keyword in node.keywords)]:
                if isinstance(argument, ast.Name):
                    writes[argument.id] = 2
    bindings = {node.targets[0].id: node.value for node in setup.body if isinstance(node, ast.Assign)
                and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                and writes[node.targets[0].id] == 1}
    aliases = _aliases(setup)
    tree, control = _last_call(payload["control_action"])
    _, target = _last_call(payload["target_action"])
    proof = {"schema": "e1c2-counterfactual-literal-control-v1", "compiled": False,
             "target_program_changed": False, "oracle_changed": False,
             "semantic_equivalence_proven": False, "status": "unsupported_or_unproven_pair"}
    if (not control or not target or ast.dump(control.func) != ast.dump(target.func)
            or len(control.args) != len(target.args)
            or [k.arg for k in control.keywords] != [k.arg for k in target.keywords]):
        return payload, proof
    pairs = [(f"arg:{n}", c, t) for n, (c, t) in enumerate(zip(control.args, target.args, strict=True))]
    pairs += [(f"kw:{c.arg}", c.value, t.value) for c, t in zip(control.keywords, target.keywords, strict=True)]
    changes = []
    for label, c, t in pairs:
        old, new = _sequence(c, bindings, aliases), _sequence(t, bindings, aliases)
        if old and new and old[0] in {"List", "Tuple"} and new[0] == "numpy_array":
            changes.append((label, c, new[1], _fingerprint(old[1]) != _fingerprint(new[1])))
        elif ast.dump(c) != ast.dump(t):
            # More than one changed factor cannot be isolated by this compiler.
            return payload, proof
    if len(changes) != 1:
        return payload, proof
    label, original, replacement, confounded = changes[0]
    original_hash = _fingerprint(original)
    if label.startswith("kw:"):
        next(k for k in control.keywords if k.arg == label[3:]).value = replacement
    else:
        control.args[int(label[4:])] = replacement
    changed = {**payload, "control_action": ast.unparse(ast.fix_missing_locations(tree))}
    if changed["target_action"] != payload["target_action"] or changed["assertion"] != payload["assertion"]:
        raise ValueError("counterfactual compiler changed target/oracle")
    name = target.func.id if isinstance(target.func, ast.Name) else target.func.attr if isinstance(target.func, ast.Attribute) else None
    guards = []
    for path, source in source_trees(frozen, workspace):
        for function in ast.walk(source):
            if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)) and function.name == name:
                for node in ast.walk(function):
                    if isinstance(node, ast.If) and any(isinstance(child, ast.Raise) for statement in node.body for child in ast.walk(statement)):
                        guards.append({"path": path, "line": node.lineno, "predicate": ast.unparse(node.test)[:1000]})
    proof.update({"compiled": True, "status": "confounded_container_values" if confounded else "same_literal_values",
                  "changed_argument": label, "original_control_argument_sha256": original_hash,
                  "literal_value_tree_sha256": _fingerprint(replacement), "literal_length": len(replacement.elts),
                  "source_guards": guards[:12], "preconditions_verified": False,
                  "precondition_check": "execute_derived_control_twice_on_unchanged_production"})
    return changed, proof
