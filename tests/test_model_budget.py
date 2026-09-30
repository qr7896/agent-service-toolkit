import json

import httpx
import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI

from agents.model_budget import (
    AmbiguousProviderCall,
    ProviderBudgetExceeded,
    _bind_with_output_limit,
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


def test_deepseek_output_cap_uses_provider_field_without_losing_thinking_setting():
    model = ChatOpenAI(model="deepseek-flash", api_key="dummy", base_url="https://api.deepseek.com")
    thinking = model.bind(reasoning_effort="low", extra_body={"thinking": {"type": "enabled"}})
    for source, disabled in ((model, True), (thinking, False)):
        bound = _bind_with_output_limit(source, 6000, disabled)
        payload = bound.bound._get_request_payload([HumanMessage(content="test")], **bound.kwargs)
        assert payload["extra_body"]["max_tokens"] == 6000
        assert payload["extra_body"]["thinking"]["type"] == ("disabled" if disabled else "enabled")
        assert payload.get("max_completion_tokens") is None


@pytest.mark.asyncio
async def test_deepseek_output_cap_reaches_http_body_without_network():
    sent = {}

    def respond(request):
        sent.update(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "mock", "object": "chat.completion", "created": 0, "model": "deepseek-flash",
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        model = ChatOpenAI(model="deepseek-flash", api_key="dummy",
                           base_url="https://api.deepseek.com", http_async_client=client)
        await _bind_with_output_limit(model, 6000, True).ainvoke([HumanMessage(content="test")])
    assert sent["max_tokens"] == 6000
    assert sent["thinking"] == {"type": "disabled"}
    assert "max_completion_tokens" not in sent


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
async def test_provider_overrun_is_recorded_then_fails_closed(tmp_path):
    response = AIMessage(content="ok")
    response.usage_metadata = {"input_tokens": 4, "output_tokens": 200, "total_tokens": 204}
    ledger = tmp_path / "calls.jsonl"
    with pytest.raises(ProviderBudgetExceeded, match="over-budget usage"):
        await budgeted_ainvoke(Model(response), [HumanMessage(content="small")],
                               config(ledger), role="planner")
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    assert [row["status"] for row in rows] == ["started", "completed"]
    assert rows[-1]["over_budget"] is True and rows[-1]["total_tokens"] == 204


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


@pytest.mark.asyncio
async def test_prompt_multiplier_can_fail_closed_before_call(tmp_path):
    model = Model(AIMessage(content="unused"))
    with pytest.raises(ProviderBudgetExceeded):
        await budgeted_ainvoke(
            model,
            [HumanMessage(content="x" * 300)],
            config(
                tmp_path / "calls.jsonl",
                provider_total_token_ceiling=1000,
                provider_task_token_ceiling=1000,
                provider_prompt_reserve_multiplier=10,
            ),
            role="compact_editor",
        )
    assert model.messages is None


@pytest.mark.asyncio
async def test_tuple_messages_are_counted_before_call(tmp_path):
    model = Model(AIMessage(content="unused"))
    with pytest.raises(ProviderBudgetExceeded):
        await budgeted_ainvoke(
            model,
            [("system", "x" * 600)],
            config(
                tmp_path / "calls.jsonl",
                provider_total_token_ceiling=100,
                provider_task_token_ceiling=100,
            ),
            role="compact_editor",
        )
    assert model.messages is None
