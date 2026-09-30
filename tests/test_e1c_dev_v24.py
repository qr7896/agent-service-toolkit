from evals import e1c_dev_v24 as dev


def test_thinking_payload_contains_public_source_patch_and_counts_only():
    row = dev._cohort()[0]
    payload = dev._payload(row)
    assert row["instance_id"] in dev.TASK_IDS
    assert payload["excerpts"] and payload["prior_candidate_patch"]
    assert set(payload["prior_check_counts"]) == {
        "f2p_pass", "f2p_total", "p2p_maintained", "p2p_total"}
    assert "grade_log" not in payload and "gold_patch" not in payload
    assert dev._reserve(payload) <= dev.TASK_TOKEN_CEILING
