from pathlib import Path

import pytest

from evals.e1c_blind_boundary import AgentView, BlindBoundaryViolation
from evals.e1c_strict_v5_boundary import (
    AssertionProjectionUnsupported,
    assert_production_relative_path,
    audit_repair_visible_payload,
    project_issue,
    strict_agent_view,
)


def test_projection_removes_inline_assertions_and_test_blocks() -> None:
    statement = """Prefetch should support sliced related querysets.
def test_prefetch(self):
    rows = list(queryset)
    self.assertEqual(len(rows), 3)
The operation currently raises an error when evaluated.
"""
    result = project_issue(statement)
    assert result.status == "projected"
    assert "Prefetch should support" in result.text
    assert "currently raises an error" in result.text
    assert "assertEqual" not in result.text
    assert "def test_" not in result.text
    assert result.removed_line_count >= 2


def test_projection_rejects_evaluator_markers() -> None:
    with pytest.raises(AssertionProjectionUnsupported):
        project_issue("Please fix this. FAIL_TO_PASS = ['tests/test_hidden.py::test_x']")


def test_projection_is_deterministic() -> None:
    statement = "Natural language requirement.\nassert value == 3\nMore explanation."
    left = project_issue(statement)
    right = project_issue(statement)
    assert left.text == right.text
    assert left.sha256 == right.sha256


def test_strict_agent_view_drops_original_test_roots(tmp_path: Path) -> None:
    view = AgentView(
        instance_id="x",
        problem_statement="Fix production behavior.\nassert hidden == 1",
        workspace=tmp_path,
        original_test_roots=(tmp_path / "tests",),
    )
    strict = strict_agent_view(view)
    assert strict.original_test_roots == ()
    assert "assert hidden" not in strict.problem_statement


@pytest.mark.parametrize(
    "path",
    [
        "../tests/test_x.py",
        "tests/test_x.py",
        "pkg/testing/helper.py",
        "gold.patch",
        "pkg/grade_result.py",
    ],
)
def test_production_path_gate_rejects_test_or_oracle_paths(path: str) -> None:
    with pytest.raises(BlindBoundaryViolation):
        assert_production_relative_path(path)


def test_payload_audit_rejects_sentinel_values() -> None:
    with pytest.raises(BlindBoundaryViolation):
        audit_repair_visible_payload(
            {"issue": "normal prose", "excerpts": ["ORACLE_SENTINEL_7f9"]},
            forbidden_values=("ORACLE_SENTINEL_7f9",),
        )
