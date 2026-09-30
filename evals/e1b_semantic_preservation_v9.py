import ast

SCHEMA_VERSION = "e1b-semantic-preservation-v1"


def _constant(node):
    if isinstance(node, ast.Constant):
        return node.value
    return None


def _guard(node):
    if not isinstance(node, ast.Compare) or len(node.ops) != 1 or len(node.comparators) != 1:
        return None
    if not isinstance(node.left, ast.Name) or not isinstance(node.ops[0], (ast.Eq, ast.Is)):
        return None
    value = _constant(node.comparators[0])
    if value is None:
        return None
    return node.left.id, value


def _action(statements, variable):
    if len(statements) != 1:
        return "ambiguous"
    statement = statements[0]
    if isinstance(statement, ast.Return):
        if isinstance(statement.value, ast.Name) and statement.value.id == variable:
            return "identity"
        return "change"
    if isinstance(statement, ast.Assign):
        if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
            return "ambiguous"
        if statement.targets[0].id != variable:
            return "ambiguous"
        if isinstance(statement.value, ast.Name) and statement.value.id == variable:
            return "identity"
        return "change"
    return "ambiguous"


def audit_semantic_preservation(obligations, patch):
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
            variable, value = guard
            branches.append({"path": path, "variable": variable, "value": value, "action": _action(node.body, variable)})

    checks = []
    for obligation in obligations:
        expected = "identity" if obligation["kind"] == "identity" else "change"
        value = obligation["value"]
        candidates = [branch for branch in branches if branch["value"] == value]
        matching = [branch for branch in candidates if branch["action"] == expected]
        satisfied = len(matching) == 1 and len(candidates) == 1
        checks.append({
            "kind": obligation["kind"],
            "value": value,
            "expected_action": expected,
            "candidate_count": len(candidates),
            "satisfied": satisfied,
            "reason": "matched" if satisfied else "missing_or_ambiguous_action",
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "checks": checks,
        "unsupported_files": unsupported_files,
        "semantic_preservation_complete": bool(checks) and all(check["satisfied"] for check in checks) and not unsupported_files,
        "scope": "conservative Python AST branch/action witness; not semantic equivalence or runtime correctness",
    }


def require_semantic_preservation(obligations, patch):
    report = audit_semantic_preservation(obligations, patch)
    if not report["semantic_preservation_complete"]:
        raise ValueError("semantic-preservation witness incomplete")
    return report
