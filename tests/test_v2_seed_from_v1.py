import json

from evals.v2_seed_from_v1 import convert_v1_episode


def episode(stop=False):
    return {
        "instance_id": "task-1",
        "decision": 0,
        "split": "train",
        "cluster": "validation",
        "source_commit": "abc",
        "candidates": [
            {"action": "files", "features": {"round": 0, "tokens_spent": 0, "candidate_cost": 0.2}, "oracle_gain": 1},
            {"action": "structural", "features": {"round": 0, "tokens_spent": 0, "candidate_cost": 1.0}, "oracle_gain": 2},
        ],
        "oracle_best_action": "" if stop else "structural",
        "stop_label": stop,
    }


def test_converter_keeps_oracle_fields_out_of_runtime_state():
    record = convert_v1_episode(episode()).to_dict()
    dumped = json.dumps(record["state"])
    assert "oracle" not in dumped and "gold" not in dumped
    assert record["chosen_action"] == "structural"


def test_converter_represents_v1_stop_as_safe_candidate():
    record = convert_v1_episode(episode(stop=True)).to_dict()
    assert record["chosen_action"] == "stop"
    assert "stop" in [row["action"] for row in record["candidates"]]
