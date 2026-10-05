from types import SimpleNamespace

import pytest
from langchain_core.messages import HumanMessage

from agents.model_budget import budgeted_ainvoke
from evals.e1c_evaluation_2_production_coverage import freeze_input
from evals.e1c_evaluation_2_raw_json import RawJsonFlash, response_record


def test_owner_ranking_does_not_fill_slots_with_example_constructors(tmp_path):
    for directory in ("examples", "doc", "benchmarks", "bench"):
        folder = tmp_path / directory
        folder.mkdir()
        (folder / "noise.py").write_text("class Noise:\n    def __init__(self): pass\n", encoding="utf-8")
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "core.py").write_text("class Engine:\n    def __init__(self, option=False):\n        self.option = option\n", encoding="utf-8")
    seed = {"issue": "Engine should expose an option in Engine.__init__().", "windows": [],
            "issue_sha256": "issue", "base_commit": "a" * 40}
    result = freeze_input(seed, tmp_path)
    assert result["windows"][0]["symbol"] == "__init__"
    assert result["windows"][0]["owner"] == "Engine"
    assert result["candidate_paths"] and set(result["candidate_paths"]) == {"pkg/core.py"}


def test_linked_plain_api_name_gets_a_window_beside_class_constructor(tmp_path):
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "types.py").write_text("class Parser:\n    def __init__(self): pass\n    def one(self): pass\n    def two(self): pass\n    def three(self): pass\n", encoding="utf-8")
    (package / "utils.py").write_text("def parse_value(value):\n    return value\n", encoding="utf-8")
    seed = {"issue": "Parser fails in [parse_value](https://example.invalid/pkg/utils.py).", "windows": [],
            "issue_sha256": "issue", "base_commit": "a" * 40}
    result = freeze_input(seed, tmp_path)
    assert any(row["symbol"] == "parse_value" for row in result["windows"])


def test_module_level_api_alias_is_not_lost_by_definition_only_lookup(tmp_path):
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "utils.py").write_text("from functools import partial\ndef parse(value, mode): return value\nparse_value = partial(parse, mode=1)\n", encoding="utf-8")
    seed = {"issue": "The linked parse_value fails on valid input.", "windows": [],
            "issue_sha256": "issue", "base_commit": "a" * 40}
    result = freeze_input(seed, tmp_path)
    assert result["windows"][0]["symbol"] == "parse_value"
    assert result["windows"][0]["origin"] == "public_api_module_alias"


def test_reported_version_name_prefix_is_only_a_production_retrieval_hint(tmp_path):
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "utils.py").write_text("def parse_value(value):\n    return value\n", encoding="utf-8")
    seed = {"issue": "The older reported parse_value_timestamp fails.", "windows": [],
            "issue_sha256": "issue", "base_commit": "a" * 40}
    assert any(row["symbol"] == "parse_value" for row in freeze_input(seed, tmp_path)["windows"])


@pytest.mark.asyncio
async def test_truncated_json_keeps_content_and_completed_budget_usage(tmp_path):
    calls = []

    class Raw:
        def parse(self):
            return {"model": "deepseek-flash", "choices": [{"message": {"role": "assistant", "content": '{"source":'},
                    "finish_reason": "length", "index": 0}], "usage": {"prompt_tokens": 10, "completion_tokens": 30, "total_tokens": 40}}

    async def create(**kwargs):
        calls.append(kwargs)
        return Raw()

    model = RawJsonFlash(model="deepseek-flash", api_key="test-only-not-a-provider-key", max_retries=0,
                         model_kwargs={"response_format": {"type": "json_object"}})
    model.async_client = SimpleNamespace(with_raw_response=SimpleNamespace(create=create))
    ledger = tmp_path / "calls.jsonl"
    response = await budgeted_ainvoke(model, [HumanMessage(content="Return JSON.")], {"configurable": {
        "provider_ledger_path": str(ledger), "provider_run_id": "synthetic", "provider_task_id": "synthetic",
        # The serialized message envelope reserves 93 tokens in this synthetic fixture.
        "provider_total_token_ceiling": 100, "provider_task_token_ceiling": 100, "provider_max_output_tokens": 30,
    }}, role="synthetic")
    result = response_record(response)
    assert len(calls) == 1 and calls[0]["response_format"] == {"type": "json_object"}
    assert result["response_status"] == "truncated" and result["raw"] == '{"source":'
    assert result["usage"]["total_tokens"] == 40
    assert '"status": "completed"' in ledger.read_text(encoding="utf-8")
