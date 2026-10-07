import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agents.model_budget import ProviderBudgetExceeded
from evals import e1c_evaluation_2_bounded_repro_dev_v4 as runner
from evals.e1c_blind_boundary import BlindBoundaryViolation


def test_explicit_last_request_and_exact_actual_previous_action():
    prior = '{"type":"json_object","retrieve":"Engine.apply"}'
    observation = {"query": "Engine.apply", "matches": 1}
    original = [SystemMessage(content="trusted"), HumanMessage(content='{"issue":"public issue"}')]
    messages = runner.conversation(original, 2, prior, observation)
    assert len(original) == 2 and isinstance(messages[-3], AIMessage) and messages[-3].content == prior
    assert json.loads(messages[-2].content.split("\n", 1)[1]) == observation
    assert "turn 2/4" in messages[-1].content and "Do not repeat" in messages[-1].content
    assert messages[0].content == "trusted"


def test_hidden_answer_and_oversized_history_stop_before_provider():
    with pytest.raises(BlindBoundaryViolation):
        runner.conversation([], 2, "action", {"test_patch": "hidden"})
    with pytest.raises(ProviderBudgetExceeded):
        runner.conversation([HumanMessage(content="x" * 36001)], 1)


@pytest.mark.asyncio
async def test_real_saved_action_and_feedback_bound_to_next_call(tmp_path, monkeypatch):
    folder = tmp_path / "task" / "turn-1"
    folder.mkdir(parents=True)
    raw = '{"retrieve":"Engine.apply"}'
    (folder / "response.json").write_text(json.dumps({"raw": raw}), encoding="utf-8")
    (folder / "feedback.json").write_text(json.dumps({"query": "Engine.apply", "matches": 1}), encoding="utf-8")
    monkeypatch.setattr(runner, "OUT", tmp_path)
    observed = []

    async def invoke(model, messages, config, *, role):
        observed.append(messages)
        return "response"

    monkeypatch.setattr(runner, "capped_invoke", invoke)
    result = await runner.budgeted_invoke(None, [], {"configurable": {"provider_task_id": "task"}}, role="e1c2_bounded_turn_2")
    assert result == "response" and observed[0][-3].content == raw
