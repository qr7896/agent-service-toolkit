from evals.serbench_v2_compatible import (
    METHOD_DIRECT,
    METHOD_FROZEN,
    direct_sufficiency,
    rank_state,
    state_features,
)


def row():
    return {
        "state_id": "s",
        "issue": "fix alpha",
        "trajectory_prefix": [{"action_type": "repo_search"}],
        "candidate_evidence": [
            {
                "evidence_id": "seen",
                "content_excerpt": "alpha",
                "source_path": "src/a.py",
                "source_type": "repo_chunk",
                "observed_by_state": True,
            },
            {
                "evidence_id": "new",
                "content_excerpt": "alpha fix",
                "source_path": "src/b.py",
                "source_type": "repo_chunk",
                "observed_by_state": False,
            },
        ],
    }


def test_direct_port_stops_on_existing_runtime_rule():
    value = row()
    assert direct_sufficiency(value)
    assert state_features(value).actions_tried == 1
    assert rank_state(value, METHOD_DIRECT)["ranked_evidence_ids"] == []


def test_candidate_correction_suppresses_observed_without_gold():
    ranked = rank_state(row(), METHOD_FROZEN)["ranked_evidence_ids"]
    assert ranked == ["new"]
