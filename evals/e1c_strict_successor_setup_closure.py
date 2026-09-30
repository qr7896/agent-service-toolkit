"""Generic issue-snippet setup-closure analysis for strict E1-C successor development."""

from __future__ import annotations

import ast
import builtins
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioCandidate:
    source: str
    free_names: tuple[str, ...]
    closed: bool
    origin: str
    behavioral: bool
    recovered_names: tuple[str, ...] = ()


_FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.IGNORECASE | re.DOTALL)


def _bound_names(tree: ast.AST) -> set[str]:
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, ast.arg):
            bound.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            bound.add(node.id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                bound.add(alias.asname or alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bound.add(alias.asname or alias.name)
    return bound


def free_names(source: str) -> tuple[str, ...]:
    tree = ast.parse(source)
    bound = _bound_names(tree)
    builtin_names = set(dir(builtins))
    loaded = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    return tuple(sorted(loaded - bound - builtin_names))


def _behavioral(source: str) -> bool:
    tree = ast.parse(source)
    return any(isinstance(node, ast.Call) for node in ast.walk(tree))


_NUMBERED_ASSIGNMENT = re.compile(
    r"(?m)^\s*(?:[-=>]+\s*)?(?:\d+\s+)?([A-Za-z_]\w*)\s*=\s*(.+?)\s*$"
)


def close_with_public_assignments(
    problem_statement: str, candidate: ScenarioCandidate
) -> ScenarioCandidate:
    """Close unresolved local setup only from simple assignments visible in the issue.

    This deliberately ignores tests, Gold, grader output, and task identity. A recovered
    assignment must bind one currently-free name and the combined source must strictly
    reduce the unresolved-name set.
    """
    if candidate.closed or not candidate.free_names:
        return candidate
    unresolved = set(candidate.free_names)
    recovered: list[str] = []
    recovered_names: list[str] = []
    for match in _NUMBERED_ASSIGNMENT.finditer(problem_statement):
        name, rhs = match.groups()
        if name not in unresolved or name in recovered_names:
            continue
        line = f"{name} = {rhs}"
        try:
            tree = ast.parse(line)
        except SyntaxError:
            continue
        if len(tree.body) != 1 or not isinstance(tree.body[0], ast.Assign):
            continue
        recovered.append(line)
        recovered_names.append(name)
    if not recovered:
        return candidate

    lines = candidate.source.splitlines()
    insert_at = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from ") or not stripped:
            insert_at = index + 1
            continue
        break
    combined_lines = lines[:insert_at] + recovered + lines[insert_at:]
    combined = "\n".join(combined_lines)
    try:
        remaining = free_names(combined)
    except SyntaxError:
        return candidate
    if len(remaining) >= len(candidate.free_names):
        return candidate
    return ScenarioCandidate(
        source=combined,
        free_names=remaining,
        closed=not remaining,
        origin=f"{candidate.origin}+public_assignment_closure",
        behavioral=_behavioral(combined),
        recovered_names=tuple(sorted(recovered_names)),
    )


def _paragraph_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.strip():
            current.append(line)
        elif current:
            blocks.append("\n".join(current))
            current = []
    if current:
        blocks.append("\n".join(current))
    return blocks


def extract_candidates(problem_statement: str) -> list[ScenarioCandidate]:
    raw: list[tuple[str, str]] = []
    for match in _FENCE.finditer(problem_statement):
        raw.append(("fenced", match.group(1).strip()))
    if not raw:
        for block in _paragraph_blocks(problem_statement):
            if re.search(r"(?m)^\s*(def |class |from |import |[A-Za-z_]\w*\s*=)", block):
                raw.append(("paragraph", block.strip()))
    out: list[ScenarioCandidate] = []
    seen: set[str] = set()
    for origin, source in raw:
        if not source or source in seen:
            continue
        seen.add(source)
        try:
            names = free_names(source)
        except SyntaxError:
            continue
        out.append(
            ScenarioCandidate(
                source=source,
                free_names=names,
                closed=not names,
                origin=origin,
                behavioral=_behavioral(source),
            )
        )
    return out
