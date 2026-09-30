"""Render strict-v7 executable typed witnesses without benchmark-specific setup."""

from __future__ import annotations

import ast
import json
from pathlib import PurePosixPath


def _module_from_path(path: str) -> str:
    pure = PurePosixPath(path.replace("\\", "/"))
    if pure.suffix != ".py":
        raise ValueError("strict-v7 executable witness requires Python production path")
    parts = list(pure.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    if not parts or any(not part.isidentifier() for part in parts):
        raise ValueError("strict-v7 candidate path is not importable")
    return ".".join(parts)


def _parse_call(source: str) -> ast.Call:
    try:
        tree = ast.parse(source.strip(), mode="eval")
    except SyntaxError as exc:
        raise ValueError("strict-v7 call_result source is not a single expression") from exc
    if not isinstance(tree.body, ast.Call) or not isinstance(tree.body.func, ast.Name):
        raise ValueError("strict-v7 call_result requires direct function call")
    for arg in tree.body.args:
        try:
            ast.literal_eval(arg)
        except (ValueError, TypeError) as exc:
            raise ValueError("strict-v7 call_result arguments must be literals") from exc
    if tree.body.keywords:
        raise ValueError("strict-v7 call_result keywords are not supported")
    return tree.body


def _literal(text: str):
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError) as exc:
        raise ValueError("strict-v7 expected value must be a literal") from exc


def render_call_result(witness: dict) -> str:
    source = str(witness["source"]).strip()
    call = _parse_call(source)
    symbol = call.func.id
    module = _module_from_path(str(witness["candidate_path"]))
    observable = str(witness["observable"])
    if ":" not in observable:
        raise ValueError("strict-v7 call_result observable is malformed")
    relation, expected_text = observable.split(":", 1)
    expected = _literal(expected_text)
    if relation not in {"return_equals", "contains", "not_contains"}:
        raise ValueError("strict-v7 call_result relation unsupported")
    call_text = ast.unparse(call)
    predicate = {
        "return_equals": "observed == expected",
        "contains": "expected in observed",
        "not_contains": "expected not in observed",
    }[relation]
    rendered = (
        "import importlib\n"
        f"module = importlib.import_module({json.dumps(module)})\n"
        f"target = getattr(module, {json.dumps(symbol)})\n"
        f"observed = {call_text.replace(symbol, 'target', 1)}\n"
        f"expected = {repr(expected)}\n"
        f"assert {predicate}\n"
        "print('STRICT_V7_CONTRACT_SATISFIED')\n"
    )
    compile(rendered, "<strict-v7-call-result>", "exec")
    return rendered


def render_python_scenario(witness: dict, import_map: dict[str, str]) -> str:
    source = str(witness["source"])
    ast.parse(source)
    imports = []
    for symbol, path in sorted(import_map.items()):
        if not symbol.isidentifier():
            raise ValueError("strict-v7 scenario import symbol invalid")
        module = _module_from_path(path)
        imports.append(
            f"{symbol} = getattr(importlib.import_module({json.dumps(module)}), {json.dumps(symbol)})"
        )
    rendered = "import importlib\n" + "\n".join(imports) + "\n" + source
    compile(rendered, "<strict-v7-python-scenario>", "exec")
    return rendered


def docker_command(witness: dict, image: str, *, import_map: dict[str, str] | None = None) -> list[str]:
    if not image or any(char.isspace() for char in image):
        raise ValueError("strict-v7 image is invalid")
    kind = witness.get("kind")
    if kind == "call_result":
        source = render_call_result(witness)
    elif kind == "python_scenario":
        source = render_python_scenario(witness, import_map or {})
    else:
        raise ValueError("strict-v7 witness kind is not executable yet")
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
        source,
    ]
