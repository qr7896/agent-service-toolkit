import asyncio
import json
from types import SimpleNamespace

from langchain_core.messages import AIMessage

from evals import e1c_evaluation_2_hybrid_dev_v3 as dev


def test_explicit_abstention_stops_without_paid_fallback():
    assert not dev.should_fallback({"status": "abstained", "reason": "no grounded oracle"})
    assert dev.should_fallback({"status": "fixture_or_positive_control_failed"})
    assert not dev.should_fallback({"status": "executed", "repeatable_nonsetup_failure": True})


def test_exact_production_anchor_not_test_or_escape(tmp_path, monkeypatch):
    package = tmp_path / "pkg"
    package.mkdir()
    source = package / "api.py"
    source.write_bytes(("x = 0\n" * 70 + "def target():\n    return x\n").encode())
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "answer.py").write_bytes(b"assert False\n")
    issue = "Problem around line `71` in `pkg/api.py`; ignore tests/answer.py and ../outside.py"
    seed = {"issue": issue, "issue_sha256": "fixture", "base_commit": "fixture"}
    monkeypatch.setattr(dev.runtime.coverage, "freeze_input", lambda *_: {**seed, "windows": [], "input_sha256": "old"})
    value = dev.path_input(seed, tmp_path)
    assert value["candidate_paths"] == ["pkg/api.py"]
    row = value["windows"][0]
    assert row["start_line"] == 59
    assert "def target" in row["text"]
    assert row["origin"] == "exact_issue_production_path"
    assert row["source_sha256"] == dev._sha(source)


def test_runner_abstention_makes_only_one_request(tmp_path, monkeypatch):
    frozen = {"tasks": [{"environment": {"missing_optional_import": None}}]}
    (tmp_path / "freeze.json").write_bytes(json.dumps(frozen).encode())
    monkeypatch.setattr(dev, "OUT", tmp_path)
    monkeypatch.setattr(dev, "preflight", lambda: frozen)
    monkeypatch.setattr(dev, "inputs", lambda: [("fixture__fixture-1", {}, tmp_path, tmp_path, "fixture")])
    monkeypatch.setattr(dev.runtime, "settings", SimpleNamespace(DEEPSEEK_API_KEY="test-not-a-key"))
    monkeypatch.setattr(dev.runtime, "model_messages", lambda *_: [])
    requests = []

    class FakeModel:
        def __init__(self, **kwargs):
            pass

        def bind(self, **kwargs):
            return self

    async def invoke(*args, **kwargs):
        requests.append(kwargs["role"])
        return AIMessage(content='{"abstain_reason":"No grounded observable expectation"}', response_metadata={"finish_reason": "stop"})

    monkeypatch.setattr(dev.runtime, "RawJsonFlash", FakeModel)
    monkeypatch.setattr(dev.runtime, "budgeted_ainvoke", invoke)
    result = asyncio.run(dev.run())
    assert result["status"] == "completed"
    assert requests == ["e1c2_hybrid_B"]
    state = json.loads((tmp_path / "state.json").read_bytes())
    assert state["rows"][0]["status"] == "abstained"
    assert not (tmp_path / "fixture__fixture-1/A/response.json").exists()
