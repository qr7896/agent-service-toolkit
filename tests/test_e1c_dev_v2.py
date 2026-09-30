import asyncio

from evals import e1c_dev_v2 as dev


def test_new_identity_and_bounded_config():
    assert dev.RUN_ID != "e1c-n30-7d8e6569"
    assert dev.RUN_DIR != dev.OUT / "e1c-n30-7d8e6569"
    first = dev._config("public-task")["configurable"]
    second = dev._config("public-task", second=True)["configurable"]
    assert first["provider_max_calls_per_task"] == 2
    assert first["provider_total_token_ceiling"] == 120_000
    assert first["provider_task_token_ceiling"] == second["provider_task_token_ceiling"] == 4_000
    assert (first["provider_max_output_tokens"], second["provider_max_output_tokens"]) == (600, 400)


def test_noop_never_reaches_official_grader(tmp_path, monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("unchanged code must not be graded")

    monkeypatch.setattr(dev, "grade", forbidden)
    value = {"excerpts": [{"path": "module.py"}]}
    result, failure = dev._attempt("public-task", tmp_path, '{"edits":[]}', value, "first", tmp_path)
    assert (result["schema"], failure) == ("e1c-dev-v2-noop", "no_edits")
    assert not (tmp_path / "grade.first.json").exists()


def test_invalid_path_still_blocked_before_grading(tmp_path, monkeypatch):
    monkeypatch.setattr(dev, "grade", lambda *_args: (_ for _ in ()).throw(AssertionError()))
    value = {"excerpts": [{"path": "module.py"}]}
    raw = '{"edits":[{"path":"secret.py","old":"a","new":"b"}]}'
    result, failure = dev._attempt("public-task", tmp_path, raw, value, "first", tmp_path)
    assert not result["resolved"]
    assert failure.startswith("patch_failure:PermissionError")


def test_noop_uses_second_call_without_first_docker_grade(tmp_path, monkeypatch):
    source = tmp_path / "module.py"
    source.write_text("old value\n", encoding="utf-8")
    monkeypatch.setattr(dev, "RUN_DIR", tmp_path / "run")
    monkeypatch.setattr(dev, "_workspace", lambda _row: tmp_path)
    monkeypatch.setattr(dev, "_payload", lambda *_args: {
        "task": "fix value", "source_commit": "base", "statement_sha256": "x",
        "statement_truncated": False,
        "excerpts": [{"path": "module.py", "start_line": 1, "text": "old value\n"}],
    })
    replies = iter(('{"edits":[]}',
                    '{"edits":[{"path":"module.py","old":"old value","new":"new value"}]}'))

    async def fake_call(*_args, **_kwargs):
        return next(replies), {"total_tokens": 10}

    grades = []

    def fake_grade(_instance_id, stage, _patch, _artifacts):
        grades.append(stage)
        return {"resolved": True, "guard_output_tail": ""}

    monkeypatch.setattr(dev, "_call", fake_call)
    monkeypatch.setattr(dev, "_patch", lambda _workspace, path: path.write_bytes(b"diff"))
    monkeypatch.setattr(dev, "grade", fake_grade)
    result = asyncio.run(dev._task({"instance_id": "public-task", "base_commit": "base"}))
    assert result["model_calls"] == 2
    assert result["resolved"]
    assert result["first_grade"]["schema"] == "e1c-dev-v2-noop"
    assert grades == ["final"]
    assert source.read_text(encoding="utf-8") == "new value\n"
