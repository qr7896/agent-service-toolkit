"""Bounded, public-only test additions from an E1-C task's test.patch."""

from __future__ import annotations

from pathlib import Path


def added_test_lines(patch: str, *, max_chars: int = 2600, max_lines: int = 70) -> str:
    """Show changed public test code, never diff metadata or removed lines."""
    if max_chars < 100 or max_lines < 1:
        raise ValueError("invalid public-test excerpt limit")
    current = ""
    selected: list[str] = []
    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            continue
        if not line.startswith("+") or line.startswith("+++ ") or not current:
            continue
        if not (current.endswith(".py") and
                ("test" in Path(current).name.lower() or "test" in Path(current).parts)):
            continue
        selected.append(f"{current}: {line[1:]}")
        if len(selected) >= max_lines:
            break
    value = "\n".join(selected)
    return value[:max_chars]
