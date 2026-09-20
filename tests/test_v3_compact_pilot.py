import pytest

from evals.v3_compact_pilot import (
    COMPACT_TASKS,
    MAX_OUTPUT_TOKENS,
    TASK_TOKEN_CEILING,
    TOTAL_TOKEN_CEILING,
    VISIBLE_RANGES,
    _apply_edits,
    _parse_edits,
)


def test_compact_pilot_is_one_small_call_per_task():
    assert TOTAL_TOKEN_CEILING == 12_000
    assert TASK_TOKEN_CEILING == 4_000
    assert MAX_OUTPUT_TOKENS == 600
    assert len(COMPACT_TASKS) == 5
    assert set(VISIBLE_RANGES) == {task.instance_id for task in COMPACT_TASKS}


def test_exact_edit_parser_and_apply(tmp_path):
    target = tmp_path / "pyproject.toml"
    target.write_text('pythonpath = ["src"]\n', encoding="utf-8")
    raw = '{"edits":[{"path":"pyproject.toml","old":"[\\"src\\"]","new":"[\\"src\\", \\".\\"]"}]}'
    edits = _parse_edits(raw, {"pyproject.toml"})
    assert _apply_edits(tmp_path, edits) == ["pyproject.toml"]
    assert target.read_text(encoding="utf-8") == 'pythonpath = ["src", "."]\n'


def test_compact_parser_blocks_unexposed_path():
    raw = '{"edits":[{"path":"src/hidden.py","old":"a","new":"b"}]}'
    with pytest.raises(PermissionError, match="not exposed"):
        _parse_edits(raw, {"pyproject.toml"})
