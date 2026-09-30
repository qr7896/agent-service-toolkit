"""Bounded source-window feedback for the existing E1-C DEV agent loop."""

from __future__ import annotations

import json
from pathlib import Path

from evals.e1c_dev_v31 import _allowed_path


def _window(workspace: Path, path: str, hints: list[str], origin: str) -> dict | None:
    if not _allowed_path(workspace, path):
        return None
    source = workspace / path
    if source.stat().st_size > 1_000_000:
        return None
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    hits = [(len(hint), index) for hint in hints if len(hint) >= 3
            for index, line in enumerate(lines) if hint in line]
    at = max(hits)[1] if hits else 0
    start = max(0, at - 35)
    return {"path": path, "start_line": start + 1,
            "text": "\n".join(lines[start:min(len(lines), at + 65)])[:5000], "origin": origin}


def extend(workspace: Path, windows: list[dict], paths: list[str], raw: str, feedback: str) -> str:
    """Append one safe source window after a search or rejected edit, never a guessed edit."""
    try:
        action = json.loads(raw)
    except (ValueError, TypeError):
        return feedback
    if not isinstance(action, dict):
        return feedback
    shown = {(item["path"], item["start_line"]) for item in windows}
    if "search" in action and isinstance(action["search"], dict):
        query = action["search"].get("query", "")
        if not isinstance(query, str) or not query.isidentifier():
            return feedback
        candidates = paths
        hints = [query]
        origin = "aci_search_auto_view"
    elif "edits" in action and feedback.startswith("Action rejected:"):
        edits = action["edits"]
        if not isinstance(edits, list) or not edits or not isinstance(edits[0], dict):
            return feedback
        path, old = edits[0].get("path"), edits[0].get("old")
        if not isinstance(path, str) or not isinstance(old, str):
            return feedback
        candidates = [path]
        hints = [line.strip() for line in old.splitlines() if len(line.strip()) >= 8]
        origin = "aci_rejected_edit_original_source"
    else:
        return feedback
    for path in candidates:
        item = _window(workspace, path, hints, origin)
        if item is not None and (item["path"], item["start_line"]) not in shown:
            windows.append(item)
            return feedback + f" Original-base source window added for {path}."
    return feedback + " No new safe source window was available."
