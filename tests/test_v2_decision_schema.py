import pytest

from evals.v2_decision_schema import CandidateAction, DecisionRecord, reward


def test_v2_decision_record_keeps_counterfactual_logging_fields():
    record = DecisionRecord(
        task_id="task-1",
        step=0,
        state={"remaining_actions": 3},
        candidates=(
            CandidateAction("lexical", 0.6, 0.8),
            CandidateAction("structural", 0.4, 0.7),
        ),
        chosen_action="lexical",
    ).validate()
    assert record.candidates[0].propensity == 0.6
    assert record.candidates[0].policy_score == 0.8


def test_v2_decision_record_rejects_invalid_propensity_mass():
    with pytest.raises(ValueError, match="sum to 1"):
        DecisionRecord(
            task_id="task-1",
            step=0,
            state={},
            candidates=(CandidateAction("lexical", 0.8, 1.0),),
            chosen_action="lexical",
        ).validate()


def test_v2_reward_matches_frozen_formula():
    value = reward(2, 100, 1, 0.2, token_weight=0.001, call_weight=0.1, risk_weight=0.5)
    assert value == pytest.approx(1.7)
