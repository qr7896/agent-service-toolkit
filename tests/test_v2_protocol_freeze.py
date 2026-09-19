import json

import pytest

from evals.v2_decision_log import DecisionJSONLWriter
from evals.v2_decision_schema import (
    FROZEN_REWARD_V1,
    SAFE_EXPLORATION_ACTIONS,
    CandidateAction,
    DecisionRecord,
    RewardConfig,
    reward,
    uniform_candidates,
)


def test_safe_exploration_excludes_write_and_shell():
    assert "write" not in SAFE_EXPLORATION_ACTIONS
    assert "shell" not in SAFE_EXPLORATION_ACTIONS


def test_reward_config_has_stable_fingerprint():
    assert FROZEN_REWARD_V1.fingerprint() == RewardConfig().fingerprint()
    assert len(FROZEN_REWARD_V1.fingerprint()) == 64


def test_uniform_candidates_are_valid_propensities():
    candidates = uniform_candidates(["files", "lexical", "structural"], {"lexical": 0.8})
    assert sum(row.propensity for row in candidates) == pytest.approx(1.0)
    assert candidates[1].policy_score == 0.8


def test_decision_jsonl_roundtrip(tmp_path):
    path = tmp_path / "decisions.jsonl"
    record = DecisionRecord(
        task_id="task-1",
        step=2,
        state={"remaining_actions": 2},
        candidates=uniform_candidates(["lexical", "stop"]),
        chosen_action="lexical",
    )
    writer = DecisionJSONLWriter(path)
    payload = writer.append(record)
    assert writer.read_all() == [payload]
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == "v2-decision-v1"


def test_decision_rejects_unsafe_candidate():
    with pytest.raises(ValueError, match="safe"):
        DecisionRecord(
            task_id="task-1",
            step=0,
            state={},
            candidates=(CandidateAction("write", 1.0, 1.0),),
            chosen_action="write",
        ).validate()


def test_frozen_reward_config_is_default():
    assert reward(2, 100, 1, 0.2) == pytest.approx(1.7)
