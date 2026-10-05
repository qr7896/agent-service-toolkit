import hashlib
import json
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

from evals import e1c_evaluation_2_hybrid_dev as hybrid


def test_bad_control_does_not_execute_target(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(hybrid, "build_source_pair", lambda *args: ({"kind": "control"}, {"kind": "target"}, {}))

    def execute(candidate, *args, **kwargs):
        calls.append(candidate["kind"])
        return {"runs": [{"returncode": 1, "timed_out": False}]}

    monkeypatch.setattr(hybrid, "execute_candidate", execute)
    row = hybrid.execute_role("B", {}, {"base_commit": "a" * 40}, tmp_path, "image", tmp_path / "role", {"missing_optional_import": None})
    assert row["control_pass"] is False and calls == ["control", "control"]


@pytest.mark.asyncio
async def test_fallback_is_one_additional_strategy_then_candidate_locks(tmp_path, monkeypatch):
    frozen = {"tasks": [{"instance_id": "synthetic", "environment": {"missing_optional_import": None}}]}
    (tmp_path / "freeze.json").write_bytes(json.dumps(frozen).encode())
    monkeypatch.setattr(hybrid, "OUT", tmp_path)
    monkeypatch.setattr(hybrid, "preflight", lambda: frozen)
    monkeypatch.setattr(hybrid, "inputs", lambda: [("synthetic", {}, tmp_path / "input", tmp_path, "image")])
    monkeypatch.setattr(hybrid, "settings", SimpleNamespace(DEEPSEEK_API_KEY="test-only"))
    monkeypatch.setattr(hybrid, "model_messages", lambda frozen, role: role)
    roles = []

    class Model:
        def __init__(self, **kwargs):
            pass

        def bind(self, **kwargs):
            return self

    async def invoke(model, messages, config, *, role):
        roles.append(messages)
        raw = '{"abstain_reason":"no contract"}' if messages == "B" else '{"source":"assert False"}'
        return AIMessage(content=raw, response_metadata={"finish_reason": "stop", "model_name": "deepseek-flash"},
                         usage_metadata={"input_tokens": 10, "output_tokens": 10, "total_tokens": 20})

    def execute(role, payload, frozen, workspace, image, root, environment):
        source = b"assert False\n"
        digest = hashlib.sha256(source).hexdigest()
        (root / "execution").mkdir(parents=True)
        (root / "execution" / f"{digest}.py").write_bytes(source)
        hybrid._save(root / "candidate.json", {"source": source.decode(), "probe_sha256": digest})
        hybrid._save(root / "execution.json", {})
        return {"status": "executed", "repeatable_failure_candidate": True, "repeatable_nonsetup_failure": False}

    monkeypatch.setattr(hybrid, "RawJsonFlash", Model)
    monkeypatch.setattr(hybrid, "budgeted_ainvoke", invoke)
    monkeypatch.setattr(hybrid, "execute_role", execute)
    assert (await hybrid.run())["status"] == "completed"
    state = json.loads((tmp_path / "state.json").read_bytes())
    assert roles == ["B", "A"] and state["rows"][0]["selected_role"] == "A"
    assert len(state["rows"][0]["roles"]) == 2
