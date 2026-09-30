from pathlib import Path

import pytest

from evals.e1c_blind_boundary import (
    BlindBoundaryViolation,
    assert_agent_path,
    assert_agent_payload,
    audit_serialized_agent_trace,
    build_agent_view,
    build_evaluator_view,
    dump_agent_trace,
)


def test_agent_view_contains_only_issue_base_and_original_tests(tmp_path: Path) -> None:
    workspace = tmp_path / "base"
    tests = workspace / "tests"
    tests.mkdir(parents=True)
    view = build_agent_view(
        instance_id="repo__issue-1",
        problem_statement="Fix the parser edge case.",
        workspace=workspace,
        original_test_roots=(tests,),
    )
    assert view.workspace == workspace.resolve()
    assert view.original_test_roots == (tests.resolve(),)
    assert not hasattr(view, "task_dir")
    assert not hasattr(view, "artifact_dir")


def test_evaluator_view_is_separate_from_agent_view(tmp_path: Path) -> None:
    task = tmp_path / "oracle"
    task.mkdir()
    evaluator = build_evaluator_view(
        instance_id="repo__issue-1",
        task_dir=task,
        artifact_dir=tmp_path / "grades",
    )
    assert evaluator.task_dir == task.resolve()
    assert not hasattr(evaluator, "workspace")
    assert not hasattr(evaluator, "problem_statement")


@pytest.mark.parametrize(
    "payload",
    [
        {"FAIL_TO_PASS": ["tests/test_hidden.py::test_case"]},
        {"nested": {"test_patch": "assert hidden"}},
        {"grade_log": "resolved"},
        {"candidate_patch_v21": "old answer"},
        {"selectors": ["hidden"]},
    ],
)
def test_agent_payload_rejects_oracle_and_historical_fields(payload: dict) -> None:
    with pytest.raises(BlindBoundaryViolation):
        assert_agent_payload(payload)


@pytest.mark.parametrize(
    "name",
    ["test.patch", "gold.patch", "tests.json", "base.log", "e1c_dev_outcome.json"],
)
def test_agent_path_rejects_oracle_named_material(tmp_path: Path, name: str) -> None:
    workspace = tmp_path / "base"
    workspace.mkdir()
    with pytest.raises(BlindBoundaryViolation):
        assert_agent_path(workspace / name, workspace=workspace)


def test_agent_path_rejects_escape_from_exact_base(tmp_path: Path) -> None:
    workspace = tmp_path / "base"
    workspace.mkdir()
    with pytest.raises(BlindBoundaryViolation):
        assert_agent_path(tmp_path / "outside.py", workspace=workspace)


def test_agent_path_allows_base_source_and_original_test(tmp_path: Path) -> None:
    workspace = tmp_path / "base"
    tests = workspace / "tests"
    source = workspace / "pkg" / "parser.py"
    tests.mkdir(parents=True)
    source.parent.mkdir()
    assert assert_agent_path(source, workspace=workspace, original_test_roots=(tests,)) == source.resolve()
    assert assert_agent_path(tests / "test_parser.py", workspace=workspace, original_test_roots=(tests,)) == (
        tests / "test_parser.py"
    ).resolve()


def test_trace_sentinel_rejects_oracle_marker() -> None:
    with pytest.raises(BlindBoundaryViolation):
        audit_serialized_agent_trace('{"note":"read test.patch for the answer"}')


def test_trace_dump_is_fail_closed(tmp_path: Path) -> None:
    output = tmp_path / "trace.json"
    with pytest.raises(BlindBoundaryViolation):
        dump_agent_trace({"official_grade": "PASS"}, output)
    assert not output.exists()


def test_trace_dump_accepts_blind_provenance(tmp_path: Path) -> None:
    output = tmp_path / "trace.json"
    dump_agent_trace(
        {"origin": "issue_statement", "path": "pkg/parser.py", "source_sha": "abc123"},
        output,
    )
    text = output.read_text(encoding="utf-8")
    assert "issue_statement" in text
    assert "official_grade" not in text
