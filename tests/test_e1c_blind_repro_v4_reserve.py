import pytest

from evals.e1c_blind_repro_v4_reserve import freeze
from evals.e1c_blind_repro_v4_selector import CONTAMINATED_IDS, reserve_status


def _row(instance_id: str, digit: str) -> dict:
    return {
        "instance_id": instance_id,
        "repo": "owner/repo",
        "base_commit": digit * 40,
        "image": f"swebench/{instance_id}:latest",
    }


def test_freeze_selects_three_disjoint_metadata_only_rows(tmp_path) -> None:
    output = tmp_path / "reserve.json"
    rows = [_row("fresh-a", "a"), _row("fresh-b", "b"), _row("fresh-c", "c"), _row("fresh-d", "d")]
    result = freeze(rows, source_revision="dataset-revision", output=output)
    assert result["task_count"] == 3
    assert result["provider_calls"] == 0
    assert result["statement_content_inspected_before_freeze"] is False
    assert reserve_status(output)["ready"] is True


def test_freeze_rejects_task_content_fields(tmp_path) -> None:
    rows = [_row("fresh-a", "a"), _row("fresh-b", "b"), _row("fresh-c", "c")]
    rows[0]["problem_statement"] = "must never enter metadata freeze"
    with pytest.raises(ValueError, match="forbidden"):
        freeze(rows, source_revision="dataset-revision", output=tmp_path / "reserve.json")


def test_web_exposed_candidates_are_quarantined() -> None:
    assert {"astropy__astropy-14539", "pytest-dev__pytest-7373", "sympy__sympy-20590"} <= CONTAMINATED_IDS
