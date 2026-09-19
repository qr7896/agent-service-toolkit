from evals.v3_frozen_pipeline_smoke import run_frozen_pipeline


def test_synthetic_nonsealed_frozen_pipeline_connects_end_to_end():
    base = {
        "source_repo": "synthetic/repo",
        "changed_paths": [],
        "experience_hits": [],
        "experience_ids": [],
        "adopted_experience_ids": None,
        "adoption_observed": False,
    }
    rows = [
        {
            **base,
            "id": "a",
            "ended_at": "2026-01-01T00:00:00+00:00",
            "source_commit_at_execution": "c1",
            "task": "fix route",
            "status": "succeeded",
        },
        {
            **base,
            "id": "b",
            "ended_at": "2026-01-02T00:00:00+00:00",
            "source_commit_at_execution": "c2",
            "task": "fix route",
            "status": "failed",
        },
        {
            **base,
            "id": "c",
            "ended_at": "2026-01-03T00:00:00+00:00",
            "source_commit_at_execution": "c3",
            "task": "fix route",
            "status": "failed",
        },
    ]
    artifact = run_frozen_pipeline(rows, {("c1", "c2"): 1, ("c1", "c3"): 2, ("c2", "c3"): 1})
    assert artifact["ready"] is True
    assert len(artifact["replay"]["windows"]) == 3
    assert len(artifact["ablation"]["samples"]) == 3
    assert artifact["counterfactual"]["ready_pairs"] == 1
    assert "no efficacy" in artifact["claim_boundary"]
