import asyncio
import json
from types import SimpleNamespace

from langchain_core.messages import AIMessage

from evals import e1c_evaluation_2_counterfactual_canary_v4 as canary


def test_canary_abstention_stops_and_never_borrows_dev_budget(tmp_path, monkeypatch):
    frame = {"tasks": [{"environment": {"missing_optional_import": None}}]}
    (tmp_path / "freeze.json").write_bytes(json.dumps(frame).encode())
    runtime = canary.runtime
    monkeypatch.setattr(runtime, "OUT", tmp_path)
    monkeypatch.setattr(runtime, "preflight", lambda: frame)
    monkeypatch.setattr(runtime, "inputs", lambda: [("fixture__fixture-1", {}, tmp_path, tmp_path, "image")])
    monkeypatch.setattr(runtime, "settings", SimpleNamespace(DEEPSEEK_API_KEY="test-not-a-key"))
    monkeypatch.setattr(runtime, "model_messages", lambda *_: [])
    calls = []

    class FakeModel:
        def __init__(self, **kwargs):
            pass

        def bind(self, **kwargs):
            return self

    async def invoke(model, messages, config, **kwargs):
        calls.append(config["configurable"])
        return AIMessage(content='{"abstain_reason":"No grounded observable behavior"}', response_metadata={"finish_reason": "stop"})

    monkeypatch.setattr(runtime, "RawJsonFlash", FakeModel)
    monkeypatch.setattr(runtime, "budgeted_ainvoke", invoke)
    result = asyncio.run(canary.run())
    assert result["fixed_denominator"] == 3 and len(calls) == 1
    assert calls[0]["provider_total_token_ceiling"] == 60000
    assert calls[0]["provider_task_token_ceiling"] == 20000
    assert calls[0]["provider_max_calls_per_task"] == 2
    assert json.loads((tmp_path / "state.json").read_bytes())["rows"][0]["status"] == "abstained"
    assert not (tmp_path / "fixture__fixture-1/A").exists()
