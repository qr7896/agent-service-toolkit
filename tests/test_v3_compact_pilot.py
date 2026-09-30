import pytest

import evals.v3_compact_pilot as compact
from evals.v3_compact_pilot import (
    COMPACT_TASKS,
    MAX_CALLS_PER_TASK,
    MAX_OUTPUT_TOKENS,
    TASK_TOKEN_CEILING,
    TOTAL_TOKEN_CEILING,
    VISIBLE_RANGES,
    _apply_edits,
    _escalation_card,
    _parse_edits,
)


def test_run_identity_is_manifest_driven():
    compact._configure_run("v3-prospective-compact-003")
    assert compact.RUN_ID == "v3-prospective-compact-003"
    assert compact.RUN_DIR == compact.ROOT / ".codex" / "v3" / "compact-003"
    assert compact.LEDGER == compact.RUN_DIR / "provider_calls.jsonl"
    compact._configure_run("v3-prospective-compact-002")


def test_compact_pilot_is_one_small_call_per_task():
    assert TOTAL_TOKEN_CEILING == 12_000
    assert TASK_TOKEN_CEILING == 4_000
    assert MAX_OUTPUT_TOKENS == 600
    assert MAX_CALLS_PER_TASK == 2
    assert len(COMPACT_TASKS) == 6
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


def test_escalation_cards_do_not_embed_development_hidden_contracts():
    text = _escalation_card("missing_symbol", {"stdout": "ImportError: cannot import name 'helper'", "stderr": ""})
    assert "usage_metadata" not in text
    assert "response_metadata" not in text
    text = _escalation_card("interface_contract", {"stdout": "object is not callable", "stderr": ""})
    assert "record(**row)" not in text
    assert "chosen_action" not in text
    text = _escalation_card("preservation_contract", {"stdout": "AssertionError", "stderr": ""})
    assert "restore_paths" not in text
    assert "onexc" not in text
