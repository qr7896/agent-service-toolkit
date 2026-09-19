from evals.v3_counterfactual_replay import build_counterfactual_replay


def test_counterfactual_replay_requires_past_positive_and_negative():
    rows = [
        {
            "id": "p",
            "ended_at": "2026-01-01T00:00:00+00:00",
            "status": "succeeded",
            "task": "fix route",
            "source_repo": "r",
            "source_commit_at_execution": "c1",
            "changed_paths": [],
        },
        {
            "id": "n",
            "ended_at": "2026-01-02T00:00:00+00:00",
            "status": "failed",
            "task": "fix route",
            "source_repo": "r",
            "source_commit_at_execution": "c2",
            "changed_paths": [],
        },
        {
            "id": "q",
            "ended_at": "2026-01-03T00:00:00+00:00",
            "status": "failed",
            "task": "fix route",
            "source_repo": "r",
            "source_commit_at_execution": "c3",
            "changed_paths": [],
        },
    ]
    artifact = build_counterfactual_replay(rows)
    assert artifact["samples"][1]["counterfactual_ready"] is False
    assert artifact["samples"][2]["counterfactual_ready"] is True
    assert artifact["ready_pairs"] == 1
    assert artifact["matched_ready_pairs"] == 1
    assert "no causal" in artifact["claim_boundary"]
