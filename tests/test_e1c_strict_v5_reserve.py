import pytest

from evals.e1c_strict_v5_reserve import freeze
from evals.e1c_strict_v5_selector import PRIOR_CONTAMINATED_IDS, reserve_status


def _row(instance_id: str, digit: str) -> dict:
    return {
        "instance_id": instance_id,
        "repo": "owner/repo",
        "base_commit": digit * 40,
        "image": f"swebench/{instance_id}:latest",
    }


def test_strict_v5_freeze_is_metadata_only_and_deterministic(tmp_path) -> None:
    rows = [
        _row("fresh-a", "a"),
        _row("fresh-b", "b"),
        _row("fresh-c", "c"),
        _row("fresh-d", "d"),
    ]
    left = tmp_path / "left.json"
    right = tmp_path / "right.json"
    a = freeze(rows, source_revision="rev-1", output=left)
    b = freeze(list(reversed(rows)), source_revision="rev-1", output=right)
    assert a["instance_ids"] == b["instance_ids"]
    assert a["provider_calls"] == 0
    assert a["statement_content_inspected_before_freeze"] is False
    assert reserve_status(left)["ready"] is True


def test_strict_v5_freeze_rejects_task_content(tmp_path) -> None:
    rows = [_row("fresh-a", "a"), _row("fresh-b", "b"), _row("fresh-c", "c")]
    rows[0]["test_patch"] = "forbidden"
    with pytest.raises(ValueError, match="forbidden"):
        freeze(rows, source_revision="rev", output=tmp_path / "reserve.json")


def test_strict_v5_freeze_excludes_prior_contaminated_identity(tmp_path) -> None:
    contaminated = next(iter(PRIOR_CONTAMINATED_IDS))
    rows = [
        _row(contaminated, "a"),
        _row("fresh-b", "b"),
        _row("fresh-c", "c"),
        _row("fresh-d", "d"),
    ]
    result = freeze(rows, source_revision="rev", output=tmp_path / "reserve.json")
    assert contaminated not in result["instance_ids"]
