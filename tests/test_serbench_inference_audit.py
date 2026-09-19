from evals.serbench_inference_audit import audit


def test_inference_only():
    r = audit(
        [
            {
                "state_id": "s",
                "repo": "owner/repo",
                "state_type": "after_search",
                "candidate_evidence": [{"evidence_id": "e"}],
                "observed_evidence_ids": [],
            }
        ]
    )
    assert r["inference_ready"] and r["states"] == 1 and r["repositories"] == 1
    assert r["stages"] == {"after_search": 1}
