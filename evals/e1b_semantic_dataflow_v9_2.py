import ast
import hashlib
import json

SCHEMA_VERSION = "e1b-semantic-dataflow-v1"


def _literal(node):
    if not isinstance(node, ast.Constant) or type(node.value) not in (str, bool, int):
        return None
    return (type(node.value).__name__, node.value)


def _same_literal(left, right):
    return left is not None and right is not None and left == right


def _effects(statements):
    risky = (ast.Call, ast.Attribute, ast.Subscript, ast.AugAssign, ast.Delete, ast.Raise, ast.Yield, ast.YieldFrom, ast.Await)
    return sorted({type(node).__name__ for statement in statements for node in ast.walk(statement) if isinstance(node, risky)})


def _aliases_before(statements):
    aliases = {}
    for statement in statements:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue
        target = statement.targets[0]
        if isinstance(target, ast.Name) and isinstance(statement.value, ast.Name):
            aliases[target.id] = aliases.get(statement.value.id, statement.value.id)
    return aliases


def _resolve(name, aliases):
    seen = set()
    while name in aliases and name not in seen:
        seen.add(name)
        name = aliases[name]
    return name


def _action(body, guarded_name, aliases):
    effects = _effects(body)
    if effects:
        return {"class": "ambiguous", "value": None, "effects": effects, "reason": "risky_effect"}
    if len(body) != 1:
        return {"class": "ambiguous", "value": None, "effects": [], "reason": "multi_action"}
    statement = body[0]
    if isinstance(statement, ast.Return):
        if isinstance(statement.value, ast.Name) and _resolve(statement.value.id, aliases) == _resolve(guarded_name, aliases):
            return {"class": "identity", "value": None, "effects": [], "reason": "return_source_alias"}
        value = _literal(statement.value)
        return {"class": "change", "value": value, "effects": [], "reason": "return_literal" if value else "dynamic_return"}
    return {"class": "ambiguous", "value": None, "effects": [], "reason": "unsupported_action"}


def _if_branches(function, path):
    aliases = {}
    rows = []
    for statement in function.body:
        if isinstance(statement, ast.Assign):
            aliases.update(_aliases_before([statement]))
            continue
        if not isinstance(statement, ast.If):
            continue
        test = statement.test
        if not isinstance(test, ast.Compare) or len(test.ops) != 1 or len(test.comparators) != 1:
            continue
        if not isinstance(test.left, ast.Name) or not isinstance(test.ops[0], (ast.Eq, ast.Is)):
            continue
        value = _literal(test.comparators[0])
        if value is None:
            continue
        rows.append({
            "path": path,
            "construct": "if",
            "variable": _resolve(test.left.id, aliases),
            "source_value": value,
            **_action(statement.body, test.left.id, aliases),
        })
    return rows


def _match_branches(function, path):
    rows = []
    for statement in function.body:
        if not isinstance(statement, ast.Match) or not isinstance(statement.subject, ast.Name):
            continue
        for case in statement.cases:
            if not isinstance(case.pattern, ast.MatchValue):
                continue
            value = _literal(case.pattern.value)
            if value is None or case.guard is not None:
                continue
            rows.append({
                "path": path,
                "construct": "match",
                "variable": statement.subject.id,
                "source_value": value,
                **_action(case.body, statement.subject.id, {}),
            })
    return rows


def _dict_branches(function, path):
    mappings = {}
    rows = []
    for statement in function.body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
            if isinstance(statement.value, ast.Dict):
                pairs = [(_literal(key), _literal(value)) for key, value in zip(statement.value.keys, statement.value.values, strict=True)]
                if pairs and all(key is not None and value is not None for key, value in pairs):
                    mappings[statement.targets[0].id] = pairs
        if isinstance(statement, ast.Return) and isinstance(statement.value, ast.Subscript):
            if isinstance(statement.value.value, ast.Name) and isinstance(statement.value.slice, ast.Name):
                for source, target in mappings.get(statement.value.value.id, []):
                    rows.append({
                        "path": path,
                        "construct": "dict_lookup",
                        "variable": statement.value.slice.id,
                        "source_value": source,
                        "class": "identity" if source == target else "change",
                        "value": target,
                        "effects": [],
                        "reason": "static_literal_mapping",
                    })
    return rows


def audit_semantic_dataflow(obligations, patch):
    branches = []
    unsupported = []
    for path, content in sorted(patch.items()):
        if not path.endswith(".py"):
            unsupported.append(path)
            continue
        try:
            tree = ast.parse(content)
        except SyntaxError:
            unsupported.append(path)
            continue
        for function in [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            branches.extend(_if_branches(function, path))
            branches.extend(_match_branches(function, path))
            branches.extend(_dict_branches(function, path))
    branches.sort(key=lambda row: (row["path"], row["construct"], row["variable"], repr(row["source_value"])))
    checks = []
    for obligation in sorted(obligations, key=lambda row: (repr(row.get("source_value")), row["kind"], repr(row.get("target_value")))):
        source = (type(obligation.get("source_value")).__name__, obligation.get("source_value"))
        expected = "identity" if obligation["kind"] == "identity" else "change"
        target_supplied = "target_value" in obligation
        target = (type(obligation.get("target_value")).__name__, obligation.get("target_value")) if target_supplied else None
        candidates = [row for row in branches if _same_literal(row["source_value"], source)]
        matching = [row for row in candidates if row["class"] == expected and not row["effects"] and (not target_supplied or (row["value"] == target if expected == "change" else target == source))]
        satisfied = len(candidates) == len(matching) == 1
        checks.append({
            "kind": obligation["kind"],
            "source_value": source,
            "target_value": target,
            "target_verification": "exact" if target_supplied else "unavailable",
            "candidate_count": len(candidates),
            "satisfied": satisfied,
            "reason": "matched" if satisfied else "missing_ambiguous_wrong_target_or_effect",
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "checks": checks,
        "branches": branches,
        "unsupported_files": sorted(unsupported),
        "complete": bool(checks) and all(row["satisfied"] for row in checks) and not unsupported,
        "provenance": "synthetic/public obligations + deterministic Python AST",
    }


def corpus_sha256(cases):
    payload = json.dumps(cases, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()
