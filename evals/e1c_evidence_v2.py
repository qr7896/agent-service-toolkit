"""Task-agnostic, issue-anchored source excerpts for a new E1-C DEV identity.

Only public issue text and the frozen base checkout are inspected. Test and
gold-patch files are intentionally excluded.
"""

from __future__ import annotations

import re
from pathlib import Path

from evals.e1c_evidence import SKIP, _terms

_PATH = re.compile(r"[A-Za-z0-9_./\\-]+\.py\b")
_SYMBOL = re.compile(r"\b(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)\b|\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def _anchors(statement: str) -> tuple[list[str], list[str]]:
    paths = list(dict.fromkeys(match.replace("\\", "/").lower() for match in _PATH.findall(statement)))
    symbols = []
    title = statement.splitlines()[0]
    for symbol in re.findall(r"__[A-Za-z0-9_]+__|\b[A-Za-z_][A-Za-z0-9_]*_[A-Za-z0-9_]+\b", title):
        if len(symbol) >= 4 and symbol not in symbols:
            symbols.append(symbol)
    for symbol in re.findall(r"\b[A-Z][a-z]+(?:[A-Z][A-Za-z0-9]+)+\b", title):
        if not symbol.endswith(("Error", "Exception")) and symbol not in symbols:
            symbols.append(symbol)
    for symbol in re.findall(r":\s*in\s+([A-Za-z_][A-Za-z0-9_]*)", statement):
        if len(symbol) >= 4 and symbol not in symbols:
            symbols.append(symbol)
    for match in _SYMBOL.finditer(statement):
        symbol = next(part for part in match.groups() if part)
        if len(symbol) >= 4 and symbol not in symbols:
            symbols.append(symbol)
    for symbol in re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", statement):
        if len(symbol) >= 4 and symbol not in symbols:
            symbols.append(symbol)
    return paths, symbols[:24]


def _window(lines: list[str], at: int, max_chars: int) -> tuple[int, str]:
    start = max(0, at - 5)
    # Keep the anchor visible even for long preceding lines.
    while start < at and len("\n".join(lines[start : at + 1])) > max_chars // 2:
        start += 1
    return start + 1, "\n".join(lines[start : at + 30])[:max_chars]


def excerpts(
    statement: str, workspace: Path, max_files: int = 4, max_chars: int = 1200
) -> list[dict]:
    paths, symbols = _anchors(statement)
    lowered_symbols = [symbol.lower() for symbol in symbols]
    terms = _terms(statement)
    title_terms = _terms(statement.splitlines()[0])
    title = statement.splitlines()[0].lower()
    traceback = "traceback" in statement.lower() or "error collecting" in statement.lower()
    ranked = []
    for path in workspace.rglob("*.py"):
        relative = path.relative_to(workspace)
        if (any(part.lower() in SKIP for part in relative.parts)
                or path.name.startswith("test_") or path.name.endswith("_test.py")
                or path.is_symlink()):
            continue
        try:
            with path.open(encoding="utf-8") as source:
                lines = source.read(100_000).splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        name = relative.as_posix().lower()
        path_score = 0
        for index, mentioned in enumerate(paths):
            order_score = index if traceback else len(paths) - index
            normalized = mentioned.lstrip("./")
            if (mentioned == name or mentioned.endswith("/" + name)
                    or name == normalized or name.endswith("/" + normalized)):
                path_score = max(path_score, 150 + 25 * order_score)
            elif mentioned.endswith("/" + relative.name.lower()):
                path_score = max(path_score, 60 + 10 * order_score)
        path_matched = path_score >= 60
        stem = path.stem.lower()
        path_score += sum(200 if term == stem else 100 if term + "s" == stem else 0
                          for term in title_terms if len(term) >= 7)
        path_score += sum(8 for symbol in lowered_symbols if symbol in name)
        path_score += sum(2 for term in terms if term in name)
        best_score, best_at = 0, 0
        for at, line in enumerate(lines):
            low = line.lower()
            score = 0
            stripped = low.lstrip()
            for lowered in lowered_symbols:
                if lowered not in low:
                    continue
                if (stripped.startswith(f"def {lowered}(")
                        or stripped.startswith(f"async def {lowered}(")
                        or stripped.startswith(f"class {lowered}(")
                        or stripped.startswith(f"class {lowered}:")):
                    score += 120 if lowered in title else 50
                elif f"{lowered}(" in low:
                    score += 18
                else:
                    score += 4
            score += sum(1 for term in terms if term in low)
            if score > best_score:
                best_score, best_at = score, at
        total = path_score + best_score
        if total:
            start, excerpt = _window(lines, best_at, max_chars)
            ranked.append((-total, name, start, excerpt, path_matched))
    if any(row[4] for row in ranked):
        ranked = [row for row in ranked if row[4]]
    ranked.sort()
    return [
        {"path": name, "start_line": start, "text": excerpt}
        for _, name, start, excerpt, _ in ranked[:max_files]
    ]
