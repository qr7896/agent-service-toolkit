"""Strict-v6 task-agnostic behavioral witness extraction from projected prose."""

from __future__ import annotations

import ast
import hashlib
import json
import re

from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

_LITERAL = r"(?:None|True|False|-?\d+(?:\.\d+)?|'[^'\n]*'|\"[^\"\n]*\")"
_CALL = r"(?P<call>[A-Za-z_]\w*\([^()\n]{0,180}\))"
_RETURN = re.compile(
    rf"(?i){_CALL}\s+(?:should|must|is expected to)\s+(?:return|returns|be|equal)\s+(?P<expected>{_LITERAL})"
)
_INSTEAD = re.compile(
    rf"(?i){_CALL}\s+(?:currently\s+)?returns?\s+(?P<actual>{_LITERAL})\s+instead\s+of\s+(?P<expected>{_LITERAL})"
)
_EQUALS = re.compile(
    rf"(?i){_CALL}\s*(?:==|should equal|must equal)\s*(?P<expected>{_LITERAL})"
)
_CONTAINS = re.compile(
    rf"(?i){_CALL}\s+(?:should|must)\s+(?P<neg>not\s+)?contain\s+(?P<expected>{_LITERAL})"
)
_RAISE = re.compile(
    rf"(?i){_CALL}\s+(?:should|must|is expected to)\s+raise\s+(?P<expected>[A-Z]\w*(?:Error|Exception))"
)
_RAISE_INSTEAD = re.compile(
    rf"(?i){_CALL}\s+raises?\s+(?P<actual>[A-Z]\w*(?:Error|Exception))\s+instead\s+of\s+(?P<expected>[A-Z]\w*(?:Error|Exception))"
)


def _safe_call(source: str) -> str | None:
    try:
        node = ast.parse(source, mode="eval").body
    except SyntaxError:
        return None
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.keywords:
        return None
    for arg in node.args:
        try:
            ast.literal_eval(arg)
        except (ValueError, TypeError):
            return None
    return node.func.id


def _matches(projected_issue: str) -> list[tuple[int, str, re.Match[str]]]:
    found = []
    for relation, pattern in (
        ("return_equals", _RETURN),
        ("return_equals", _INSTEAD),
        ("return_equals", _EQUALS),
        ("contains", _CONTAINS),
        ("raises", _RAISE),
        ("raises", _RAISE_INSTEAD),
    ):
        for match in pattern.finditer(projected_issue):
            found.append((match.start(), relation, match))
    found.sort(key=lambda item: (item[0], item[1], item[2].group("call")))
    return found


def candidate_witnesses(projected_issue: str, localization: dict, *, limit: int = 5) -> list[dict]:
    candidates = localization.get("candidates", [])
    witnesses = []
    seen: set[tuple[str, str, str, str]] = set()
    for _, relation, match in _matches(projected_issue):
        call = match.group("call")
        symbol = _safe_call(call)
        if symbol is None:
            continue
        expected = match.group("expected")
        negated = bool(match.groupdict().get("neg"))
        matched_paths = [
            row for row in candidates
            if row.get("symbol") == symbol
            or f"def {symbol}(" in str(row.get("text", ""))
        ]
        for row in matched_paths:
            path = str(row["path"])
            if not path.endswith(".py"):
                continue
            module_parts = path[:-3].split("/")
            if module_parts[-1] == "__init__":
                module_parts = module_parts[:-1]
            if not module_parts or any(not part.isidentifier() for part in module_parts):
                continue
            module = ".".join(module_parts)
            relation_name = "not_contains" if relation == "contains" and negated else relation
            key = (module, call, relation_name, expected)
            if key in seen:
                continue
            seen.add(key)
            witness = {
                "kind": "strict_v6_natural_language_witness",
                "relation": relation_name,
                "call": call,
                "expected": expected,
                "symbol": symbol,
                "module": module,
                "candidate_path": path,
                "source_sha256": row["source_sha256"],
                "provenance": "projected_issue_plus_production_localization",
                "benchmark_assertion_used": False,
                "task_id_used": False,
            }
            witness["witness_sha256"] = audit_repair_visible_payload(witness)
            witnesses.append(witness)
            if len(witnesses) == limit:
                return witnesses
    return witnesses


def render_witness(witness: dict) -> str:
    module = json.dumps(witness["module"])
    symbol = json.dumps(witness["symbol"])
    call = witness["call"]
    relation = witness["relation"]
    expected = witness["expected"]
    call_expr = "target(" + call.split("(", 1)[1]
    prefix = (
        "import importlib\n"
        f"module = importlib.import_module({module})\n"
        f"target = getattr(module, {symbol})\n"
    )
    if relation == "raises":
        body = (
            "try:\n"
            f"    {call_expr}\n"
            "except Exception as exc:\n"
            f"    if type(exc).__name__ == {json.dumps(expected)}:\n"
            "        print('STRICT_V6_CONTRACT_SATISFIED')\n"
            "        raise SystemExit(0)\n"
            "    print('STRICT_V6_CONTRACT_MISMATCH:unexpected_exception:' + type(exc).__name__)\n"
            "    raise SystemExit(8)\n"
            "print('STRICT_V6_CONTRACT_MISMATCH:no_exception')\n"
            "raise SystemExit(8)\n"
        )
    else:
        if relation == "return_equals":
            predicate = "observed == expected"
        elif relation == "contains":
            predicate = "expected in observed"
        elif relation == "not_contains":
            predicate = "expected not in observed"
        else:
            raise ValueError(f"unsupported strict-v6 witness relation: {relation}")
        body = (
            "try:\n"
            f"    observed = {call_expr}\n"
            "except Exception as exc:\n"
            "    print('STRICT_V6_OBSERVED_EXCEPTION:' + type(exc).__name__)\n"
            "    raise SystemExit(7)\n"
            f"expected = {expected}\n"
            f"if not ({predicate}):\n"
            f"    print('STRICT_V6_CONTRACT_MISMATCH:{relation}')\n"
            "    raise SystemExit(8)\n"
            "print('STRICT_V6_CONTRACT_SATISFIED')\n"
        )
    source = prefix + body
    compile(source, "<strict-v6-witness>", "exec")
    return source


def docker_witness_command(witness: dict, image: str) -> list[str]:
    if not isinstance(image, str) or not image or any(char.isspace() for char in image):
        raise ValueError("invalid strict-v6 image")
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--workdir",
        "/testbed",
        image,
        "python",
        "-X",
        "utf8",
        "-c",
        render_witness(witness),
    ]


def freeze_witness_plan(projected_issue: str, localization: dict) -> dict:
    witnesses = candidate_witnesses(projected_issue, localization)
    value = {
        "schema": "e1c-strict-v6-witness-plan-v1",
        "status": "candidate_executable_witnesses" if witnesses else "no_reproducer",
        "witnesses": witnesses,
        "trusted_reproducer": False,
        "no_reproducer_reason": None if witnesses else "no_safe_behavioral_relation",
    }
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    value["plan_sha256"] = hashlib.sha256(encoded.encode()).hexdigest()
    audit_repair_visible_payload(value)
    return value
