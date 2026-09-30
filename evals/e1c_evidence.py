"""Frozen, task-agnostic bounded source excerpts for E1-C SWE-bench tasks."""

from __future__ import annotations

import re
from pathlib import Path

SKIP = {".git", ".venv", "venv", "test", "tests", "testing", "docs", "build", "dist"}
STOP = {
    "about",
    "after",
    "also",
    "been",
    "before",
    "being",
    "between",
    "could",
    "does",
    "from",
    "have",
    "into",
    "instead",
    "should",
    "their",
    "there",
    "these",
    "this",
    "when",
    "where",
    "which",
    "while",
    "with",
    "would",
    "your",
    "that",
    "than",
    "some",
    "such",
    "only",
    "using",
    "used",
    "return",
    "returns",
    "error",
    "value",
    "values",
    "test",
    "tests",
    "python",
    "issue",
    "code",
    "function",
    "class",
}


def _terms(statement: str) -> list[str]:
    quoted = re.findall(r"`([A-Za-z_][A-Za-z0-9_.]{2,})`", statement)
    raw = [*quoted, *re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", statement)]
    result: list[str] = []
    for item in raw:
        for part in item.split("."):
            term = part.lower()
            if len(term) >= 4 and term not in STOP and term not in result:
                result.append(term)
            if len(result) == 16:
                return result
    return result


def excerpts(
    statement: str, workspace: Path, max_files: int = 4, max_chars: int = 1200
) -> list[dict]:
    terms = _terms(statement)
    ranked = []
    for path in workspace.rglob("*.py"):
        relative = path.relative_to(workspace)
        if any(part.lower() in SKIP for part in relative.parts) or path.is_symlink():
            continue
        try:
            with path.open(encoding="utf-8") as source:
                text = source.read(30_000)
        except (UnicodeDecodeError, OSError):
            continue
        low, name = text.lower(), relative.as_posix().lower()
        score = sum(5 * (term in name) + min(3, low.count(term)) for term in terms)
        if score:
            ranked.append((-score, relative.as_posix(), text))
    ranked.sort()
    result = []
    for _, relative, text in ranked[:max_files]:
        lines = text.splitlines()
        needle = next((term for term in terms if term in text.lower()), "")
        at = next((i for i, line in enumerate(lines) if needle in line.lower()), 0)
        start = max(0, at - 15)
        window = "\n".join(lines[start : at + 25])[:max_chars]
        result.append({"path": relative, "start_line": start + 1, "text": window})
    return result
