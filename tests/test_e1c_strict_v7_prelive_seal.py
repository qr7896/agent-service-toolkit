import json

from evals.e1c_strict_v7_prelive_seal import seal


def test_v7_seal_closes_all_downstream_gates_after_zero_of_three(tmp_path, monkeypatch) -> None:
    assessment = tmp_path / "assessment.json"
    assessment.write_text(
        json.dumps(
            {
                "identity_certificate": {"instance_ids": ["a", "b", "c"]},
                "source_ready_count": 3,
                "projection_supported_count": 3,
                "typed_candidate_task_count": 0,
                "executable_candidate_task_count": 0,
                "minimum_executable_candidate_tasks": 2,
                "summary_sha256": "a" * 64,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("evals.e1c_strict_v7_prelive_seal.ASSESSMENT", assessment)
    result = seal(output=tmp_path / "seal.json")
    assert result["candidate_gate_failed"] is True
    assert result["image_pull_allowed"] is False
    assert result["official_admission_allowed"] is False
    assert result["live_allowed"] is False
    assert result["c5_allowed"] is False
    assert result["dev30_allowed"] is False
    assert result["fresh30_allowed"] is False
    assert result["next_mechanism_must_use_new_independent_canary"] is True


def test_v7_seal_does_not_claim_decisive_failure_when_materialization_incomplete(tmp_path, monkeypatch) -> None:
    assessment = tmp_path / "assessment.json"
    assessment.write_text(
        json.dumps(
            {
                "identity_certificate": {"instance_ids": ["a", "b", "c"]},
                "source_ready_count": 2,
                "projection_supported_count": 3,
                "typed_candidate_task_count": 0,
                "executable_candidate_task_count": 0,
                "minimum_executable_candidate_tasks": 2,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("evals.e1c_strict_v7_prelive_seal.ASSESSMENT", assessment)
    result = seal(output=tmp_path / "seal.json")
    assert result["candidate_gate_failed"] is False
    assert result["decision"] == "not_sealed"
