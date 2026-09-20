import json

import pytest

from evals.v3_paired_memory_report import classify, summarize


@pytest.mark.parametrize(
    ("off_success", "on_success", "off_patch", "on_patch", "expected"),
    [
        (False, True, "a", "b", "helpful_memory"),
        (True, False, "a", "b", "harmful_memory"),
        (True, True, "same", "same", "redundant_memory"),
        (True, True, "a", "b", "behavior_changed_no_success_delta"),
    ],
)
def test_classify_covers_all_outcomes(
    off_success, on_success, off_patch, on_patch, expected
):
    off = {"success": off_success, "patch_sha256": off_patch}
    on = {"success": on_success, "patch_sha256": on_patch}
    assert classify(off, on) == expected


def test_summarize_recomputes_missing_outcome_and_keeps_claim_boundary(tmp_path):
    comparison = tmp_path / "comparison.json"
    comparison.write_text(
        json.dumps(
            {
                "results": [
                    {
                        "success": False,
                        "patch_sha256": "off",
                        "provider_usage": {"total_tokens": 100},
                        "wall_time_ms": 10,
                    },
                    {
                        "success": True,
                        "patch_sha256": "on",
                        "provider_usage": {"total_tokens": 120},
                        "wall_time_ms": 12,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    result = summarize([comparison])

    assert result["n"] == 1
    assert result["counts"]["helpful_memory"] == 1
    assert result["pairs"][0]["token_delta"] == 20
    assert "do not infer causal efficacy" in result["claim_boundary"]
