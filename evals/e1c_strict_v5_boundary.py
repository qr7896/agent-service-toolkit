"""Strict-v5 repair-visible boundary and deterministic issue projection."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evals.e1c_blind_boundary import (
    AgentView,
    BlindBoundaryViolation,
    assert_agent_payload,
    audit_forbidden_values,
    audit_serialized_agent_trace,
)

_CODE_FENCE = re.compile(r"(?ms)^\s*```[^\n]*\n.*?^\s*```\s*$")
_ASSERT_LINE = re.compile(
    r"(?i)^\s*(?:assert\b|self\.assert\w*\s*\(|pytest\.raises\s*\(|with\s+self\.assert\w*\s*\()"
)
_TEST_DEF = re.compile(r"(?i)^\s*(?:async\s+)?def\s+test[_\w]*\s*\(")
_TEST_CLASS = re.compile(r"(?i)^\s*class\s+Test\w*\s*[:(]")
_IMPORT_TEST = re.compile(r"(?i)^\s*(?:from|import)\s+(?:pytest|unittest)\b")
_PATH_SENTINEL = re.compile(r"(?i)(?:^|[/\\])(?:tests?|testing)(?:[/\\]|$)")
_EXECUTABLE_MARKERS = (
    "FAIL_TO_PASS",
    "PASS_TO_PASS",
    "test_patch",
    "gold_patch",
    "grade_log",
)


class AssertionProjectionUnsupported(BlindBoundaryViolation):
    """Raised when a statement cannot be projected without preserving test-oracle code."""


@dataclass(frozen=True)
class IssueProjection:
    status: str
    text: str
    sha256: str
    removed_line_count: int
    removed_code_block_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "e1c-strict-v5-issue-projection-v1",
            "status": self.status,
            "text": self.text,
            "sha256": self.sha256,
            "removed_line_count": self.removed_line_count,
            "removed_code_block_count": self.removed_code_block_count,
        }


def _strip_code_fences(statement: str) -> tuple[str, int]:
    removed = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal removed
        removed += 1
        block = match.group(0)
        plain = [
            line.strip()
            for line in block.splitlines()
            if line.strip()
            and not line.lstrip().startswith("```")
            and not _ASSERT_LINE.match(line)
            and not _TEST_DEF.match(line)
            and not _TEST_CLASS.match(line)
            and not _IMPORT_TEST.match(line)
        ]
        prose = [line for line in plain if not re.search(r"[=(){}\[\]:]{2,}|\b(?:def|class|return|yield)\b", line)]
        return "\n".join(prose)

    return _CODE_FENCE.sub(repl, statement), removed


def project_issue(statement: str) -> IssueProjection:
    if not isinstance(statement, str) or not statement.strip():
        raise AssertionProjectionUnsupported("assertion_projection_unsupported: empty issue")
    for marker in _EXECUTABLE_MARKERS:
        if marker.lower() in statement.lower():
            raise AssertionProjectionUnsupported(
                f"assertion_projection_unsupported: evaluator marker {marker}"
            )

    stripped, removed_blocks = _strip_code_fences(statement.replace("\r\n", "\n"))
    kept: list[str] = []
    removed_lines = 0
    in_test_body = False
    test_indent = 0

    for raw in stripped.splitlines():
        line = raw.rstrip()
        indent = len(line) - len(line.lstrip(" "))
        if in_test_body:
            if line.strip() and indent <= test_indent:
                in_test_body = False
            else:
                removed_lines += 1
                continue
        if _TEST_DEF.match(line) or _TEST_CLASS.match(line):
            in_test_body = True
            test_indent = indent
            removed_lines += 1
            continue
        if _ASSERT_LINE.match(line) or _IMPORT_TEST.match(line):
            removed_lines += 1
            continue
        if _PATH_SENTINEL.search(line) and re.search(r"(?i)\b(?:open|read|path|file|patch|test)\b", line):
            removed_lines += 1
            continue
        kept.append(line)

    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        raise AssertionProjectionUnsupported("assertion_projection_unsupported: no natural-language residue")
    if _ASSERT_LINE.search(text) or _TEST_DEF.search(text) or _TEST_CLASS.search(text):
        raise AssertionProjectionUnsupported("assertion_projection_unsupported: executable assertion residue")
    lowered = text.lower()
    if any(marker.lower() in lowered for marker in _EXECUTABLE_MARKERS):
        raise AssertionProjectionUnsupported("assertion_projection_unsupported: evaluator residue")
    digest = hashlib.sha256(text.encode()).hexdigest()
    return IssueProjection(
        status="projected",
        text=text,
        sha256=digest,
        removed_line_count=removed_lines,
        removed_code_block_count=removed_blocks,
    )


def strict_agent_view(view: AgentView) -> AgentView:
    projected = project_issue(view.problem_statement)
    return AgentView(
        instance_id=view.instance_id,
        problem_statement=projected.text,
        workspace=view.workspace,
        original_test_roots=(),
    )


def assert_production_relative_path(path: str) -> str:
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise BlindBoundaryViolation("strict-v5 path escapes production workspace")
    lowered = [part.lower() for part in candidate.parts]
    if any(part in {"test", "tests", "testing"} or part.startswith("test_") for part in lowered):
        raise BlindBoundaryViolation("strict-v5 test path rejected")
    name = candidate.name.lower()
    if name.endswith(".patch") or "gold" in name or "grade" in name:
        raise BlindBoundaryViolation("strict-v5 oracle-like path rejected")
    return candidate.as_posix()


def audit_repair_visible_payload(payload: Any, *, forbidden_values: tuple[str, ...] = ()) -> str:
    assert_agent_payload(payload)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    audit_serialized_agent_trace(encoded)
    audit_forbidden_values(encoded, forbidden_values)
    return hashlib.sha256(encoded.encode()).hexdigest()
