"""Zero-call issue/base evidence package for assertion-blind E1-C repair."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

from evals.e1c_blind_boundary import (
    assert_agent_path,
    assert_agent_payload,
    audit_serialized_agent_trace,
)
from evals.e1c_evidence_v2 import _anchors

_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,}")


def extract_contract(statement: str) -> dict:
    paths, symbols = _anchors(statement)
    sentences = [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+|\n+", statement.strip())
        if part.strip()
    ]
    obligations = [
        sentence[:500]
        for sentence in sentences
        if any(
            token in sentence.lower()
            for token in (
                "should",
                "must",
                "expected",
                "instead",
                "return",
                "raise",
                "preserve",
                "support",
                "allow",
                "avoid",
                "wrong",
                "incorrect",
                "fail",
                "error",
            )
        )
    ][:8]
    title_terms = [
        word.lower()
        for word in _WORD.findall(statement.splitlines()[0])
        if len(word) >= 5
    ][:20]
    value = {
        "schema": "e1c-blind-contract-v3",
        "explicit_paths": paths[:12],
        "symbols": symbols[:24],
        "title_terms": title_terms,
        "obligations": obligations,
        "statement_sha256": hashlib.sha256(statement.encode()).hexdigest(),
    }
    assert_agent_payload(value)
    return value


def _is_original_test(relative: Path) -> bool:
    lowered = [part.lower() for part in relative.parts]
    return (
        relative.name.startswith("test_")
        or relative.name.endswith("_test.py")
        or any(part in {"tests", "test"} for part in lowered)
    )


def discover_test_roots(workspace: Path) -> tuple[Path, ...]:
    roots: list[Path] = []
    for name in ("tests", "test"):
        candidate = workspace / name
        if candidate.is_dir():
            roots.append(candidate)
    for candidate in workspace.iterdir():
        if candidate.is_dir() and candidate.name.lower().endswith("tests") and candidate not in roots:
            roots.append(candidate)
    return tuple(sorted(roots, key=lambda path: path.as_posix()))


def discover_original_test_probes(statement: str, workspace: Path, *, limit: int = 4) -> dict:
    contract = extract_contract(statement)
    symbols = [symbol.lower() for symbol in contract["symbols"]]
    terms = {
        word.lower()
        for word in _WORD.findall(statement)
        if len(word) >= 5
    }
    ranked: list[tuple[int, str, list[str]]] = []
    for path in workspace.rglob("*.py"):
        relative = path.relative_to(workspace)
        if path.is_symlink() or not _is_original_test(relative) or path.stat().st_size > 500_000:
            continue
        try:
            path = assert_agent_path(path, workspace=workspace)
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lowered = text.lower()
        matched_symbols = [symbol for symbol in symbols if symbol in lowered]
        score = 20 * len(matched_symbols) + min(10, sum(term in lowered for term in terms))
        if score:
            ranked.append((-score, relative.as_posix(), matched_symbols[:8]))
    ranked.sort()
    probes = [
        {"path": path, "matched_symbols": matched, "origin": "exact_base_original_test"}
        for _, path, matched in ranked[:limit]
    ]
    value = {
        "schema": "e1c-blind-reproducer-plan-v2",
        "status": "existing_test_probe" if probes else "no_reproducer",
        "probes": probes,
        "generated_test": False,
        "oracle_used": False,
    }
    assert_agent_payload(value)
    return value


def _production_python(path: Path, workspace: Path) -> bool:
    relative = path.relative_to(workspace)
    return (
        path.is_file()
        and not path.is_symlink()
        and not _is_original_test(relative)
        and path.name not in {"setup.py", "conftest.py"}
        and path.stat().st_size <= 1_000_000
    )


def _definition_index(workspace: Path) -> tuple[dict[str, list[dict]], list[dict]]:
    definitions: dict[str, list[dict]] = {}
    callers: list[dict] = []
    for path in workspace.rglob("*.py"):
        if not _production_python(path, workspace):
            continue
        try:
            path = assert_agent_path(path, workspace=workspace)
            source = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)
        except (OSError, SyntaxError):
            continue
        relative = path.relative_to(workspace).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            called: set[str] = set()
            imported: set[str] = set()
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name):
                        called.add(child.func.id)
                    elif isinstance(child.func, ast.Attribute):
                        called.add(child.func.attr)
                elif isinstance(child, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in child.names)
                elif isinstance(child, ast.ImportFrom) and child.module:
                    imported.add(child.module.split(".")[0])
            item = {
                "path": relative,
                "symbol": node.name,
                "start_line": node.lineno,
                "end_line": node.end_lineno or node.lineno,
                "calls": sorted(called),
                "imports": sorted(imported),
                "source_sha256": digest,
            }
            definitions.setdefault(node.name, []).append(item)
            callers.append(item)
    return definitions, callers


def lexical_windows(statement: str, workspace: Path, *, limit: int = 4) -> list[dict]:
    contract = extract_contract(statement)
    terms = {word.lower() for word in _WORD.findall(statement) if len(word) >= 5}
    option_literals = {
        flag.lower() for flag in re.findall(r"(?<![\w-])--[A-Za-z][\w-]*", statement)
    }
    title_terms = set(contract["title_terms"])
    symbols = [symbol.lower() for symbol in contract["symbols"]]
    ranked: list[tuple[int, str, int, str, str]] = []
    for path in workspace.rglob("*.py"):
        if not _production_python(path, workspace):
            continue
        try:
            path = assert_agent_path(path, workspace=workspace)
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        relative = path.relative_to(workspace).as_posix()
        lowered_path = relative.lower()
        path_score = 0
        path_score += 40 * sum(term in lowered_path for term in title_terms)
        path_score += 12 * sum(symbol in lowered_path for symbol in symbols)
        best_score = 0
        best_at = 0
        for index, line in enumerate(source.splitlines()):
            low = line.lower()
            score = 0
            score += 100 * sum(
                re.search(rf"(?<![\w-]){re.escape(flag)}(?![\w-])", low) is not None
                for flag in option_literals
            )
            score += 14 * sum(term in low for term in title_terms)
            score += 8 * sum(symbol in low for symbol in symbols)
            score += sum(term in low for term in terms)
            if score > best_score:
                best_score, best_at = score, index
        total = path_score + best_score
        if not total:
            continue
        lines = source.splitlines()
        start = max(0, best_at - 6)
        text = "\n".join(lines[start : best_at + 34])[:2200]
        ranked.append(
            (
                -total,
                relative,
                start + 1,
                text,
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    ranked.sort()
    return [
        {
            "path": relative,
            "start_line": start,
            "end_line": start + text.count("\n"),
            "text": text,
            "symbol": None,
            "origin": "issue_lexical",
            "depth": 90,
            "source_sha256": digest,
        }
        for _, relative, start, text, digest in ranked[:limit]
    ]


def _explicit_path_match(relative: str, explicit_paths: set[str]) -> bool:
    lowered = relative.lower().lstrip("./")
    return any(
        lowered == explicit
        or lowered.endswith("/" + explicit)
        or explicit.endswith("/" + lowered)
        for explicit in explicit_paths
    )


def structural_windows(statement: str, workspace: Path, *, limit: int = 6) -> list[dict]:
    contract = extract_contract(statement)
    definitions, callers = _definition_index(workspace)
    title = statement.splitlines()[0].lower()
    explicit_paths = {path.lower().replace("\\", "/").lstrip("./") for path in contract["explicit_paths"]}
    lower_definitions: dict[str, list[dict]] = {}
    for name, items in definitions.items():
        lower_definitions.setdefault(name.lower(), []).extend(items)

    requested: dict[str, int] = {}
    for symbol in contract["symbols"]:
        key = symbol.lower()
        score = 120
        if key in title:
            score += 180
        if "_" in symbol or any(char.isupper() for char in symbol[1:]):
            score += 30
        if symbol.startswith("__") and symbol.endswith("__"):
            score -= 70
        requested[key] = max(requested.get(key, 0), score)
    for term in contract["title_terms"]:
        if term in lower_definitions:
            requested[term] = max(requested.get(term, 0), 260)

    ranked: list[tuple[int, str, int, int, str, int, str]] = []
    target_names: set[str] = set()
    for lowered_name, base_score in requested.items():
        items = lower_definitions.get(lowered_name, [])
        frequency_penalty = min(100, max(0, len(items) - 1) * 10)
        for item in items:
            score = base_score - frequency_penalty
            if _explicit_path_match(item["path"], explicit_paths):
                score += 260
            target_names.add(item["symbol"])
            ranked.append(
                (
                    -score,
                    item["path"],
                    item["start_line"],
                    item["end_line"],
                    item["symbol"],
                    0,
                    "issue_ast_definition",
                )
            )

    for item in callers:
        hits = sorted(target_names.intersection(item["calls"]))
        if hits:
            score = 100 + 15 * len(hits)
            if _explicit_path_match(item["path"], explicit_paths):
                score += 180
            ranked.append(
                (
                    -score,
                    item["path"],
                    item["start_line"],
                    item["end_line"],
                    item["symbol"],
                    1,
                    "ast_caller",
                )
            )
        if _explicit_path_match(item["path"], explicit_paths):
            ranked.append(
                (
                    -360,
                    item["path"],
                    item["start_line"],
                    item["end_line"],
                    item["symbol"],
                    0,
                    "issue_explicit_path",
                )
            )

    seen: set[tuple[str, str, int]] = set()
    structural: list[dict] = []
    for _, relative, start, end, symbol, depth, origin in sorted(ranked):
        key = (relative, symbol, depth)
        if key in seen:
            continue
        seen.add(key)
        path = workspace / relative
        try:
            path = assert_agent_path(path, workspace=workspace)
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        window_start = max(1, start - 6)
        window_end = min(len(lines), end + 8)
        structural.append(
            {
                "path": relative,
                "symbol": symbol,
                "start_line": window_start,
                "end_line": window_end,
                "text": "\n".join(lines[window_start - 1 : window_end])[:5000],
                "origin": origin,
                "depth": depth,
                "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
        if len(structural) == max(limit, 8):
            break

    lexical = lexical_windows(statement, workspace, limit=4)
    merged: list[dict] = []
    seen_items: set[tuple[str, str | None, str]] = set()
    for item in [*structural, *lexical]:
        key = (item["path"], item.get("symbol"), item["origin"])
        if key in seen_items:
            continue
        seen_items.add(key)
        merged.append(item)
        if len(merged) == limit:
            break
    return merged


def ast_windows(statement: str, workspace: Path, *, limit: int = 4) -> list[dict]:
    return structural_windows(statement, workspace, limit=limit)


def freeze_blind_evidence(statement: str, workspace: Path) -> dict:
    payload = {
        "schema": "e1c-blind-evidence-freeze-v3",
        "contract": extract_contract(statement),
        "reproducer": discover_original_test_probes(statement, workspace),
        "windows": structural_windows(statement, workspace),
    }
    assert_agent_payload(payload)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    audit_serialized_agent_trace(encoded)
    return {**payload, "evidence_sha256": hashlib.sha256(encoded.encode()).hexdigest()}

