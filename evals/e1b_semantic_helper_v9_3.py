import ast
import hashlib
import json

SCHEMA_VERSION = "e1b-semantic-helper-v1"
MAX_HELPER_DEPTH = 1


def _literal(node):
    if isinstance(node, ast.Constant) and type(node.value) in (str, bool, int):
        return type(node.value).__name__, node.value
    return None


def _unsafe(function):
    unsafe = (
        ast.Global, ast.Nonlocal, ast.Attribute, ast.Subscript, ast.AugAssign, ast.Delete,
        ast.Raise, ast.Yield, ast.YieldFrom, ast.Await, ast.Try, ast.With, ast.AsyncWith,
        ast.For, ast.AsyncFor, ast.While, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp,
    )
    return sorted({type(node).__name__ for node in ast.walk(function) if isinstance(node, unsafe)})


def _direct_calls(function):
    return sorted({
        node.func.id
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    })


def _return_action(node, parameter):
    if isinstance(node, ast.Name) and node.id == parameter:
        return "identity", None
    value = _literal(node)
    if value is not None:
        return "change", value
    return "unsupported", None


def _summary(function):
    if len(function.args.args) != 1 or function.args.vararg or function.args.kwarg:
        return None, "signature"
    parameter = function.args.args[0].arg
    unsafe = _unsafe(function)
    if unsafe:
        return None, "unsafe:" + ",".join(unsafe)
    if _direct_calls(function):
        return None, "nested_call"
    rows = []
    for statement in function.body:
        if isinstance(statement, ast.If):
            test = statement.test
            if not (
                isinstance(test, ast.Compare)
                and len(test.ops) == len(test.comparators) == 1
                and isinstance(test.left, ast.Name)
                and test.left.id == parameter
                and isinstance(test.ops[0], (ast.Eq, ast.Is))
                and len(statement.body) == 1
                and isinstance(statement.body[0], ast.Return)
            ):
                return None, "unsupported_if"
            source = _literal(test.comparators[0])
            action, target = _return_action(statement.body[0].value, parameter)
            if source is None or action == "unsupported":
                return None, "dynamic_if"
            rows.append((source, action, target))
        elif isinstance(statement, ast.Match):
            if not isinstance(statement.subject, ast.Name) or statement.subject.id != parameter:
                return None, "unsupported_match"
            for case in statement.cases:
                if case.guard is not None or not isinstance(case.pattern, ast.MatchValue) or len(case.body) != 1 or not isinstance(case.body[0], ast.Return):
                    return None, "unsupported_match"
                source = _literal(case.pattern.value)
                action, target = _return_action(case.body[0].value, parameter)
                if source is None or action == "unsupported":
                    return None, "dynamic_match"
                rows.append((source, action, target))
        elif isinstance(statement, ast.Return):
            continue
        else:
            return None, "unsupported_statement"
    if not rows:
        return None, "no_mapping"
    sources = [row[0] for row in rows]
    if len(sources) != len(set(sources)):
        return None, "conflicting_mapping"
    return rows, "supported"


def audit_helper_semantics(obligations, patch):
    functions = {}
    rejected_helpers = {}
    for path, content in sorted(patch.items()):
        if not path.endswith(".py"):
            continue
        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions[(path, node.name)] = node

    summaries = {}
    for key, function in sorted(functions.items()):
        summary, reason = _summary(function)
        if summary is None:
            rejected_helpers[f"{key[0]}::{key[1]}"] = reason
        else:
            summaries[f"{key[0]}::{key[1]}"] = [
                {"source": source, "class": action, "target": target} for source, action, target in summary
            ]

    called_helpers = {
        (path, node.value.func.id)
        for (path, _), function in functions.items()
        for node in ast.walk(function)
        if isinstance(node, ast.Return)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
    }
    call_witnesses = []
    for (path, caller_name), function in sorted(functions.items()):
        if (path, caller_name) in called_helpers:
            continue
        for node in ast.walk(function):
            if not isinstance(node, ast.Return) or not isinstance(node.value, ast.Call):
                continue
            call = node.value
            if not isinstance(call.func, ast.Name) or len(call.args) != 1 or not isinstance(call.args[0], ast.Name):
                continue
            key = f"{path}::{call.func.id}"
            if key not in summaries:
                continue
            for row in summaries[key]:
                call_witnesses.append({
                    "path": path,
                    "caller": caller_name,
                    "helper": call.func.id,
                    "depth": 1,
                    **row,
                })
    call_witnesses.sort(key=lambda row: (row["path"], row["caller"], row["helper"], repr(row["source"])))

    checks = []
    for obligation in sorted(obligations, key=lambda row: (repr(row.get("source_value")), row["kind"], repr(row.get("target_value")))):
        source = type(obligation.get("source_value")).__name__, obligation.get("source_value")
        expected = "identity" if obligation["kind"] == "identity" else "change"
        target_given = "target_value" in obligation
        target = (type(obligation.get("target_value")).__name__, obligation.get("target_value")) if target_given else None
        candidates = [row for row in call_witnesses if row["source"] == source]
        matches = [row for row in candidates if row["class"] == expected and (not target_given or (row["target"] == target if expected == "change" else target == source))]
        ok = len(candidates) == len(matches) == 1
        checks.append({
            "source": source, "kind": obligation["kind"], "target": target,
            "target_verification": "exact" if target_given else "unavailable",
            "satisfied": ok,
            "reason": "helper_summary_match" if ok else "missing_ambiguous_wrong_target_or_unsupported_helper",
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "max_helper_depth": MAX_HELPER_DEPTH,
        "checks": checks,
        "helper_summaries": summaries,
        "rejected_helpers": dict(sorted(rejected_helpers.items())),
        "call_witnesses": call_witnesses,
        "complete": bool(checks) and all(row["satisfied"] for row in checks),
        "provenance": "same-file one-hop pure helper summary from deterministic Python AST",
    }


def corpus_sha256(cases):
    raw = json.dumps(cases, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()
