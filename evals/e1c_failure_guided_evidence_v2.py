"""Resolve public failing-test imports to production definitions, without gold patches."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from evals.e1c_failure_guided_evidence import locate as locate_v1
from evals.e1c_failure_guided_evidence import windows as windows_v1

_FRAME = re.compile(r'File "/testbed/([^"\n]+\.py)"')
_DOTTED_TEST = re.compile(r"\(([^()]+)\)")


def _test_paths(log: str, selectors: list[str], workspace: Path) -> list[Path]:
    candidates = list(_FRAME.findall(log))
    for selector in selectors:
        if "::" in selector:
            candidates.append(selector.split("::", 1)[0])
        else:
            match = _DOTTED_TEST.search(selector)
            if match:
                parts = match.group(1).split(".")[:-1]
                candidates.append("tests/" + "/".join(parts) + ".py")
    result = []
    for relative in candidates:
        path = workspace / relative
        if (relative.startswith("tests/") and path.is_file() and not path.is_symlink()
                and path not in result):
            result.append(path)
    return result[:6]


def _tree(path: Path) -> ast.Module | None:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 1_000_000:
        return None
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeError):
        return None


def _module_path(workspace: Path, module: str) -> Path | None:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*(\.[A-Za-z_][A-Za-z_0-9]*)*", module):
        return None
    stem = workspace.joinpath(*module.split("."))
    for path in (stem.with_suffix(".py"), stem / "__init__.py"):
        if path.is_file() and not path.is_symlink():
            return path
    return None


def _definition(path: Path, symbol: str) -> ast.AST | None:
    tree = _tree(path)
    if tree is None:
        return None
    return next((node for node in tree.body
                 if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                 and node.name == symbol), None)


def _resolve(workspace: Path, module: str, symbol: str) -> tuple[Path, ast.AST] | None:
    path = _module_path(workspace, module)
    if path is None:
        return None
    direct = _definition(path, symbol)
    if direct is not None:
        return path, direct
    if path.name != "__init__.py":
        return None
    tree = _tree(path)
    if tree is None:
        return None
    found = []
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or not node.module or node.level:
            continue
        if not any(alias.name in ("*", symbol) for alias in node.names):
            continue
        child = _module_path(workspace, node.module)
        if child is not None and (definition := _definition(child, symbol)) is not None:
            found.append((child, definition))
    return found[0] if len(found) == 1 else None


def locate(statement: str, base_log: str, workspace: Path, selectors: list[str]) -> list[dict]:
    existing = locate_v1(statement, base_log, workspace)
    if existing:
        return existing
    ranked: dict[str, tuple[int, str]] = {}
    for test_path in _test_paths(base_log, selectors, workspace):
        tree = _tree(test_path)
        if tree is None:
            continue
        stem = test_path.stem.removeprefix("test_").lower()
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom) or not node.module or node.level:
                continue
            for alias in node.names:
                symbol = alias.name
                if len(symbol) < 5 or symbol == "*":
                    continue
                score = (10 if symbol.lower() in stem else 0) + (
                    8 if re.search(rf"\b{re.escape(symbol)}s?\b", statement, re.I) else 0)
                score += 4 if any(part in stem for part in node.module.lower().split(".")[-2:]) else 0
                selector_rank = next((index for index, selector in enumerate(selectors)
                                      if symbol.lower() in selector.lower()), None)
                if selector_rank is not None:
                    score += 6 + max(0, 3 - selector_rank)
                score += 4 if any(len(part) >= 5 and re.search(rf"\b{re.escape(part)}\b", statement, re.I)
                                  for part in node.module.split(".")[-2:]) else 0
                # A generic prose mention alone (e.g. QuerySet) is insufficient.
                if score < 10:
                    continue
                resolved = _resolve(workspace, node.module, symbol)
                if resolved is None:
                    continue
                path, _ = resolved
                relative = path.relative_to(workspace).as_posix()
                if any(part.startswith("test") for part in path.relative_to(workspace).parts):
                    continue
                ranked[relative] = max(ranked.get(relative, (0, "")), (score, symbol))
    if not ranked:
        return []
    ordered = sorted(ranked.items(), key=lambda item: (-item[1][0], item[0]))[:2]
    return [{"path": path, "confidence": 75 if score >= 12 else 60,
             "origin": "public_failing_test_import", "symbol": symbol}
            for path, (score, symbol) in ordered]


def windows(statement: str, base_log: str, workspace: Path, selectors: list[str],
            *, limit: int = 3) -> list[dict]:
    found = locate(statement, base_log, workspace, selectors)
    if not found or found[0]["origin"] != "public_failing_test_import":
        return windows_v1(statement, base_log, workspace, limit=limit)
    result = []
    for candidate in found[:limit]:
        source = workspace / candidate["path"]
        definition = _definition(source, candidate["symbol"])
        if definition is None:
            continue
        lines = source.read_text(encoding="utf-8").splitlines()
        anchor = definition
        if isinstance(definition, ast.ClassDef):
            terms = set(re.findall(r"[a-z]{4,}", (statement + " ".join(selectors)).lower().replace("_", " ")))
            methods = [(len(set(re.findall(r"[a-z]{4,}", node.name.lower().replace("_", " "))) & terms), node)
                       for node in definition.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if methods:
                score, method = max(methods, key=lambda pair: (pair[0], -pair[1].lineno))
                if score:
                    anchor = method
        start = max(0, anchor.lineno - 6)
        end = min(len(lines), max(anchor.lineno + 75,
                                  min(anchor.end_lineno or 0, anchor.lineno + 100)))
        result.append({"path": candidate["path"], "start_line": start + 1,
                       "text": "\n".join(lines[start:end])[:5000], "origin": candidate["origin"]})
    if not result:
        return windows_v1(statement, base_log, workspace, limit=limit)
    return result
