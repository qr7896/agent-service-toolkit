import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agents.model_budget import (
    AmbiguousProviderCall,
    ProviderBudgetExceeded,
    budgeted_ainvoke,
)


class Model:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.messages = None

    def bind(self, **_kwargs):
        return self

    async def ainvoke(self, messages):
        self.messages = messages
        if self.error:
            raise self.error
        return self.response


class PaymentRequired(RuntimeError):
    status_code = 402


def config(path, **overrides):
    values = {
        "provider_ledger_path": str(path),
        "provider_run_id": "run",
        "provider_task_id": "task",
        "provider_total_token_ceiling": 100,
        "provider_task_token_ceiling": 100,
        "provider_max_calls_per_task": 1,
        "provider_max_output_tokens": 10,
    }
    values.update(overrides)
    return {"configurable": values}


@pytest.mark.asyncio
async def test_budgeted_call_records_usage_and_stops_at_call_ceiling(tmp_path):
    response = AIMessage(content="ok")
    response.usage_metadata = {"input_tokens": 4, "output_tokens": 2, "total_tokens": 6}
    ledger = tmp_path / "calls.jsonl"
    messages = [HumanMessage(content="small")]

    assert await budgeted_ainvoke(Model(response), messages, config(ledger), role="planner")
    with pytest.raises(ProviderBudgetExceeded):
        await budgeted_ainvoke(Model(response), messages, config(ledger), role="coder")

    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    assert [row["status"] for row in rows] == ["started", "completed"]
    assert rows[-1]["total_tokens"] == 6


@pytest.mark.asyncio
async def test_unanswered_started_call_blocks_resume(tmp_path):
    ledger = tmp_path / "calls.jsonl"
    ledger.write_text(
        json.dumps({"run_id": "run", "task_id": "task", "call_id": "lost", "status": "started"})
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(AmbiguousProviderCall):
        await budgeted_ainvoke(
            Model(AIMessage(content="unused")),
            [HumanMessage(content="small")],
            config(ledger),
            role="planner",
        )


@pytest.mark.asyncio
async def test_known_payment_failure_can_resume_after_top_up(tmp_path):
    ledger = tmp_path / "calls.jsonl"
    messages = [HumanMessage(content="small")]
    with pytest.raises(PaymentRequired):
        await budgeted_ainvoke(
            Model(error=PaymentRequired()), messages, config(ledger), role="planner"
        )

    response = AIMessage(content="ok")
    response.usage_metadata = {"input_tokens": 4, "output_tokens": 2, "total_tokens": 6}
    assert await budgeted_ainvoke(Model(response), messages, config(ledger), role="planner")

    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    assert [row["status"] for row in rows] == ["started", "failed", "started", "completed"]


@pytest.mark.asyncio
async def test_large_tool_result_is_bounded_before_reserve_and_provider_call(tmp_path):
    response = AIMessage(content="ok")
    response.usage_metadata = {"input_tokens": 20, "output_tokens": 2, "total_tokens": 22}
    model = Model(response)
    messages = [
        HumanMessage(content="small"),
        ToolMessage(content="x" * 10_000, tool_call_id="tool-1"),
    ]
    await budgeted_ainvoke(
        model,
        messages,
        config(
            tmp_path / "calls.jsonl",
            provider_total_token_ceiling=1000,
            provider_task_token_ceiling=1000,
            provider_max_tool_result_chars=80,
        ),
        role="coder",
    )

    assert len(model.messages[1].content) == 80
    assert "tool output truncated" in model.messages[1].content


@pytest.mark.asyncio
async def test_tool_schema_reserve_blocks_coder_before_call(tmp_path):
    response = AIMessage(content="unused")
    response.usage_metadata = {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}
    model = Model(response)
    with pytest.raises(ProviderBudgetExceeded):
        await budgeted_ainvoke(
            model,
            [HumanMessage(content="small")],
            config(
                tmp_path / "calls.jsonl",
                provider_total_token_ceiling=1000,
                provider_task_token_ceiling=1000,
                provider_tool_schema_reserve_tokens=3500,
            ),
            role="coder",
        )
    assert model.messages is None
