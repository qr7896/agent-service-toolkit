import json

import pytest

from evals.e1c_strict_v5_metadata import audit_pool, freeze_file, locally_touched_ids


def _row(instance_id: str, digit: str) -> dict:
    return {
        "instance_id": instance_id,
        "repo": "owner/repo",
        "base_commit": digit * 40,
        "image": f"swebench/{instance_id}:latest",
    }


def test_metadata_audit_rejects_locally_touched_and_extra_fields() -> None:
    contaminated = next(iter(locally_touched_ids()))
    payload = {
        "source_revision": "fixed-rev",
        "tasks": [
            _row(contaminated, "a"),
            {**_row("fresh-a", "b"), "problem_statement": "forbidden"},
            _row("fresh-b", "c"),
        ],
    }
    result = audit_pool(payload)
    assert result["eligible_count"] == 1
    assert result["task_content_inspected"] is False
    assert {row["reason"] for row in result["rejected"]} == {
        "identity_locally_touched_or_prior_lineage",
        "forbidden_task_content_field",
    }


def test_freeze_file_requires_three_untouched_metadata_only_rows(tmp_path) -> None:
    source = tmp_path / "metadata.json"
    source.write_text(
        json.dumps({
            "source_revision": "external-rev-1",
            "tasks": [
                _row("unseen-aa", "a"),
                _row("unseen-bb", "b"),
                _row("unseen-cc", "c"),
                _row("unseen-dd", "d"),
            ],
        }),
        encoding="utf-8",
    )
    output = tmp_path / "reserve.json"
    result = freeze_file(source, output=output)
    assert result["task_count"] == 3
    assert result["provider_calls"] == 0
    assert result["statement_content_inspected_before_freeze"] is False


def test_metadata_audit_rejects_non_exact_schema() -> None:
    with pytest.raises(ValueError, match="metadata pool"):
        audit_pool({"source_revision": "x"})
