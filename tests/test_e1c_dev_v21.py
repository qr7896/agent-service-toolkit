import asyncio

from evals import e1c_dev_v21 as dev


def test_new_identity_and_budget():
    assert dev.RUN_ID == "e1c-dev-v21-n30-7d8e6569"
    assert dev._config("task")["configurable"]["provider_task_token_ceiling"] == 8_000
    assert dev._config("task")["configurable"]["provider_total_token_ceiling"] == 210_000
    assert dev.SOFT_TOTAL_TOKEN_CEILING == 180_000


def test_second_payload_respects_remaining_budget():
    value = {
        "task": "fix the public issue\n" * 200,
        "excerpts": [{"path": "module.py", "start_line": 1, "text": "def target():\n" * 100}],
        "escalation": {"policy": "evidence_insufficient", "evidence": "x" * 1200},
        "statement_truncated": False,
    }
    fitted = dev._fit(value, second=True, available=2_800)
    assert dev._reserve(fitted, second=True) <= 2_800


def test_insufficient_remaining_budget_skips_second_call(tmp_path, monkeypatch):
    monkeypatch.setattr(dev, "RUN_DIR", tmp_path / "run")
    monkeypatch.setattr(dev, "_workspace", lambda _row: tmp_path)
    monkeypatch.setattr(dev, "_payload", lambda *_args: {
        "task": "fix target", "source_commit": "base", "statement_sha256": "x",
        "statement_truncated": False,
        "excerpts": [{"path": "module.py", "start_line": 1, "text": "def target(): pass"}],
    })
    calls = []

    async def fake_call(*_args, **_kwargs):
        calls.append(1)
        return '{"edits":[]}', {"total_tokens": 7_900}

    monkeypatch.setattr(dev, "_call", fake_call)
    result = asyncio.run(dev._task({"instance_id": "public-task", "base_commit": "base"}))
    assert len(calls) == 1
    assert result["model_calls"] == 1
    assert result["budget_stop"]


def test_soft_limit_can_borrow_bounded_headroom(tmp_path, monkeypatch):
    monkeypatch.setattr(dev, "RUN_DIR", tmp_path / "run")
    monkeypatch.setattr(dev, "_workspace", lambda _row: tmp_path)
    monkeypatch.setattr(dev, "_payload", lambda *_args: {
        "task": "fix target", "source_commit": "base", "statement_sha256": "x",
        "statement_truncated": False,
        "excerpts": [{"path": "module.py", "start_line": 1, "text": "def target(): pass"}],
    })
    calls = []

    async def fake_call(*_args, **_kwargs):
        calls.append(1)
        return '{"edits":[]}', {"total_tokens": 5_900 if len(calls) == 1 else 10}

    monkeypatch.setattr(dev, "_call", fake_call)
    result = asyncio.run(dev._task({"instance_id": "public-task", "base_commit": "base"}))
    assert result["model_calls"] == 2
    assert result["elastic_headroom_used"]
