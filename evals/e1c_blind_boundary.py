"""Fail-closed information boundary for assertion-blind E1-C repair runs."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ORACLE_NAMES = frozenset({
    "test.patch",
    "gold.patch",
    "tests.json",
    "base.log",
    "gold.log",
    "grade.log",
})
ORACLE_FIELDS = frozenset({
    "FAIL_TO_PASS",
    "PASS_TO_PASS",
    "test_patch",
    "gold_patch",
    "base_log",
    "grade_log",
    "official_grade",
    "gold",
    "selectors",
})
HISTORICAL_HINTS = (
    "candidate_patch",
    "dev_outcome",
    "best_of",
    "public_test_evidence",
    "failure_guided_evidence",
)


class BlindBoundaryViolation(RuntimeError):
    """Raised when evaluator-only material reaches the repair-side view."""


@dataclass(frozen=True)
class AgentView:
    instance_id: str
    problem_statement: str
    workspace: Path
    original_test_roots: tuple[Path, ...]


@dataclass(frozen=True)
class EvaluatorView:
    instance_id: str
    task_dir: Path
    artifact_dir: Path


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError:
        return False
    return True


def _reject_name(path: Path) -> None:
    lowered = path.name.lower()
    if lowered in ORACLE_NAMES or any(hint in lowered for hint in HISTORICAL_HINTS):
        raise BlindBoundaryViolation(f"repair-side oracle path rejected: {path.name}")


def assert_agent_path(path: Path, *, workspace: Path, original_test_roots: Sequence[Path] = ()) -> Path:
    resolved = path.resolve(strict=False)
    allowed = _inside(resolved, workspace) or any(_inside(resolved, root) for root in original_test_roots)
    if not allowed:
        raise BlindBoundaryViolation("repair-side path escapes exact-base workspace")
    for part in resolved.parts:
        _reject_name(Path(part))
    return resolved


def read_agent_text(view: AgentView, relative_path: str, *, max_chars: int = 100_000) -> str:
    path = assert_agent_path(
        view.workspace / relative_path,
        workspace=view.workspace,
        original_test_roots=view.original_test_roots,
    )
    if not path.is_file() or path.is_symlink():
        raise BlindBoundaryViolation("repair-side read requires a regular exact-base file")
    return path.read_text(encoding="utf-8", errors="replace")[:max_chars]


def assert_agent_payload(value: Any, *, location: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text in ORACLE_FIELDS:
                raise BlindBoundaryViolation(f"repair-side oracle field rejected at {location}.{key_text}")
            if any(hint in key_text.lower() for hint in HISTORICAL_HINTS):
                raise BlindBoundaryViolation(f"repair-side historical field rejected at {location}.{key_text}")
            assert_agent_payload(item, location=f"{location}.{key_text}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            assert_agent_payload(item, location=f"{location}[{index}]")
        return
    if isinstance(value, Path):
        _reject_name(value)


def build_agent_view(
    *,
    instance_id: str,
    problem_statement: str,
    workspace: Path,
    original_test_roots: Sequence[Path] = (),
) -> AgentView:
    if not instance_id or not problem_statement.strip():
        raise ValueError("instance_id and problem_statement are required")
    workspace = workspace.resolve(strict=True)
    roots = tuple(root.resolve(strict=True) for root in original_test_roots)
    for root in roots:
        if not _inside(root, workspace):
            raise BlindBoundaryViolation("original tests must live inside exact-base workspace")
    return AgentView(instance_id, problem_statement, workspace, roots)


def build_evaluator_view(*, instance_id: str, task_dir: Path, artifact_dir: Path) -> EvaluatorView:
    if not instance_id:
        raise ValueError("instance_id is required")
    return EvaluatorView(instance_id, task_dir.resolve(strict=True), artifact_dir.resolve(strict=False))


def audit_serialized_agent_trace(text: str) -> None:
    lowered = text.lower()
    forbidden = {name.lower() for name in ORACLE_NAMES}
    forbidden.update(field.lower() for field in ORACLE_FIELDS)
    forbidden.update(HISTORICAL_HINTS)
    hits = sorted(token for token in forbidden if token in lowered)
    if hits:
        raise BlindBoundaryViolation("repair-side trace contains forbidden oracle markers: " + ", ".join(hits))


def audit_forbidden_values(text: str, forbidden_values: Sequence[str]) -> None:
    hits = [value for value in forbidden_values if value and value in text]
    if hits:
        raise BlindBoundaryViolation(f"repair-side trace contains {len(hits)} evaluator sentinel value(s)")


def dump_agent_trace(
    payload: Mapping[str, Any],
    path: Path,
    *,
    forbidden_values: Sequence[str] = (),
) -> None:
    assert_agent_payload(payload)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    audit_serialized_agent_trace(encoded)
    audit_forbidden_values(encoded, forbidden_values)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encoded + os.linesep, encoding="utf-8")

