import json
from pathlib import Path

from evals.e1c_strict_v6_prelive_seal import seal


def test_seal_closes_image_and_live_after_zero_of_three_candidate_gate(
    tmp_path: Path, monkeypatch
) -> None:
    assessment = tmp_path / "assessment.json"
    output = tmp_path / "seal.json"
    assessment.write_text(
        json.dumps(
            {
                "source_ready_count": 3,
                "projection_supported_count": 3,
                "candidate_reproducer_task_count": 0,
                "minimum_candidate_reproducer_tasks": 2,
                "summary_sha256": "a" * 64,
                "rows": [{"instance_id": f"task-{index}"} for index in range(3)],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("evals.e1c_strict_v6_prelive_seal.ASSESSMENT", assessment)
    result = seal(output=output)
    assert result["candidate_reproducer_gate_failed"] is True
    assert result["image_pull_allowed"] is False
    assert result["official_admission_allowed"] is False
    assert result["live_allowed"] is False
    assert result["same_canary_reuse_for_mechanism_tuning_allowed"] is False
    assert result["next_mechanism_must_use_new_independent_canary"] is True
    assert result["large_image_download_avoided"] is True


def test_seal_does_not_claim_decisive_failure_when_materialization_incomplete(
    tmp_path: Path, monkeypatch
) -> None:
    assessment = tmp_path / "assessment.json"
    output = tmp_path / "seal.json"
    assessment.write_text(
        json.dumps(
            {
                "source_ready_count": 2,
                "projection_supported_count": 3,
                "candidate_reproducer_task_count": 0,
                "minimum_candidate_reproducer_tasks": 2,
                "rows": [{"instance_id": f"task-{index}"} for index in range(3)],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("evals.e1c_strict_v6_prelive_seal.ASSESSMENT", assessment)
    result = seal(output=output)
    assert result["candidate_reproducer_gate_failed"] is False
    assert result["decision"] == "not_sealed"
