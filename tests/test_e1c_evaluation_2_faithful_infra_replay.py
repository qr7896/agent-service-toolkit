import asyncio
import json

from evals import e1c_evaluation_2_faithful_infra_replay as replay


def test_cached_response_uses_preserved_bytes_without_provider(tmp_path, monkeypatch):
    monkeypatch.setattr(replay, "SOURCE", tmp_path)
    path = tmp_path / "fixture__fixture-1/B/response.json"
    path.parent.mkdir(parents=True)
    value = {"raw": '{"abstain_reason":"unchanged"}', "usage": {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5},
             "finish_reason": "stop", "provider_model": "deepseek-flash"}
    path.write_bytes(json.dumps(value).encode())
    response = asyncio.run(replay.invoke_cached(None, [], {"configurable": {"provider_task_id": "fixture__fixture-1"}}, role="e1c2_hybrid_B"))
    assert response.content == value["raw"]
    record = replay.cached_record(response)
    assert record["cached_response_sha256"] == replay._sha(path)
    assert record["new_provider_calls"] == 0 and record["usage_is_upstream_not_new"]


def test_missing_role_is_controller_marker_not_new_model_call(tmp_path, monkeypatch):
    monkeypatch.setattr(replay, "SOURCE", tmp_path)
    monkeypatch.setattr(replay, "MISSES", [])
    response = asyncio.run(replay.invoke_cached(None, [], {"configurable": {"provider_task_id": "fixture__fixture-1"}}, role="e1c2_hybrid_A"))
    assert replay.cached_record(response)["controller_cache_missing"]
    assert replay.MISSES[0]["status"] == "upstream_response_not_collected"
    assert response.usage_metadata["total_tokens"] == 0
