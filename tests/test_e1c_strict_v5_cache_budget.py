import json

import evals.e1c_strict_v5_cache_budget as budget


def test_cache_budget_uses_remaining_not_total_bytes(tmp_path) -> None:
    source = tmp_path / "cache.json"
    source.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "instance_id": "x__one",
                        "ready": True,
                        "total_compressed_bytes": 2_000_000_000,
                        "remaining_compressed_bytes": 900_000_000,
                    },
                    {
                        "instance_id": "y__two",
                        "ready": True,
                        "total_compressed_bytes": 1_000_000_000,
                        "remaining_compressed_bytes": 90_000_000,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    result = budget.build(
        output=tmp_path / "out.json",
        cache_path=source,
        pull_timeout=900,
    )
    assert result["rows"][0]["required_bytes_per_second_for_budget"] == 1_000_000
    assert result["rows"][1]["required_bytes_per_second_for_budget"] == 100_000
    assert (
        result["minimum_required_bytes_per_second_for_all_missing_images"]
        == 1_000_000
    )
    assert result["changes_admission_gate"] is False
    assert result["c5_allowed"] is False


def test_cache_budget_keeps_missing_accounting_as_unknown(tmp_path) -> None:
    source = tmp_path / "cache.json"
    source.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "instance_id": "x__one",
                        "ready": False,
                        "remaining_compressed_bytes": None,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    result = budget.build(output=tmp_path / "out.json", cache_path=source)
    assert result["ready_count"] == 0
    assert result["rows"][0]["required_bytes_per_second_for_budget"] is None
    assert result["minimum_required_bytes_per_second_for_all_missing_images"] is None
