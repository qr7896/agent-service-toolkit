import ast

SCHEMA_VERSION = "e1b-semantic-effect-v1"


def _literal(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, bool, int)):
        return node.value
    return None


def _guard(node):
    if not isinstance(node, ast.Compare) or len(node.ops) != 1 or len(node.comparators) != 1:
        return None
    if not isinstance(node.left, ast.Name) or not isinstance(node.ops[0], (ast.Eq, ast.Is)):
        return None
    value = _literal(node.comparators[0])
    if value is None:
        return None
    return node.left.id, value


def _has_side_effect(statement):
    if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
        return True
    if isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        return any(isinstance(target, (ast.Attribute, ast.Subscript)) for target in targets)
    return False


def _action(statements, variable):
    if not statements or any(_has_side_effect(statement) for statement in statements):
        return {"class": "ambiguous", "value": None, "side_effect": True}
    if len(statements) != 1:
        return {"class": "ambiguous", "value": None, "side_effect": False}
    statement = statements[0]
    if isinstance(statement, ast.Return):
        if isinstance(statement.value, ast.Name) and statement.value.id == variable:
            return {"class": "identity", "value": None, "side_effect": False}
        value = _literal(statement.value)
        return {"class": "change", "value": value, "side_effect": False}
    if isinstance(statement, ast.Assign):
        if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
            return {"class": "ambiguous", "value": None, "side_effect": False}
        if statement.targets[0].id != variable:
            return {"class": "ambiguous", "value": None, "side_effect": False}
        if isinstance(statement.value, ast.Name) and statement.value.id == variable:
            return {"class": "identity", "value": None, "side_effect": False}
        return {"class": "change", "value": _literal(statement.value), "side_effect": False}
    return {"class": "ambiguous", "value": None, "side_effect": False}


def audit_semantic_effect(obligations, patch):
    branches = []
    unsupported_files = []
    for path, content in sorted(patch.items()):
        if not path.endswith(".py"):
            unsupported_files.append(path)
            continue
        try:
            tree = ast.parse(content)
        except SyntaxError:
            unsupported_files.append(path)
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.If):
                continue
            guard = _guard(node.test)
            if guard is None:
                continue
            variable, source_value = guard
            branches.append({
                "path": path,
                "variable": variable,
                "source_value": source_value,
                **_action(node.body, variable),
            })

    checks = []
    for obligation in sorted(obligations, key=lambda item: (str(item.get("source_value")), item["kind"], str(item.get("target_value")))):
        source = obligation.get("source_value")
        expected_class = "identity" if obligation["kind"] == "identity" else "change"
        target_available = "target_value" in obligation
        target = obligation.get("target_value")
        candidates = [branch for branch in branches if branch["source_value"] == source]
        matching = []
        for branch in candidates:
            class_ok = branch["class"] == expected_class and not branch["side_effect"]
            target_ok = not target_available or (branch["value"] == target if expected_class == "change" else target == source)
            if class_ok and target_ok:
                matching.append(branch)
        satisfied = len(candidates) == 1 and len(matching) == 1
        checks.append({
            "kind": obligation["kind"],
            "source_value": source,
            "target_value": target if target_available else None,
            "target_verification": "exact" if target_available else "unavailable",
            "expected_action": expected_class,
            "candidate_count": len(candidates),
            "satisfied": satisfied,
            "reason": "matched" if satisfied else "missing_ambiguous_wrong_target_or_effect",
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "checks": checks,
        "branches": sorted(branches, key=lambda item: (item["path"], str(item["source_value"]), item["variable"])),
        "unsupported_files": sorted(unsupported_files),
        "semantic_effect_complete": bool(checks) and all(check["satisfied"] for check in checks) and not unsupported_files,
        "scope": "conservative Python AST source/target/action/effect witness; not semantic equivalence or runtime correctness",
    }


def require_semantic_effect(obligations, patch):
    report = audit_semantic_effect(obligations, patch)
    if not report["semantic_effect_complete"]:
        raise ValueError("semantic-effect witness incomplete")
    return report
