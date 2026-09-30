import asyncio

import pytest

from evals import e1c_live_runner as runner


def test_frozen_identity_and_budget() -> None:
    manifest = runner._manifest()
    assert len(manifest["tasks"]) == 30
    assert len({row["instance_id"] for row in manifest["tasks"]}) == 30
    first = runner._config("public-task")["configurable"]
    second = runner._config("public-task", escalation=True)["configurable"]
    assert first["provider_task_token_ceiling"] == second["provider_task_token_ceiling"] == 4000
    assert first["provider_total_token_ceiling"] == 120_000
    assert first["provider_max_calls_per_task"] == 2
    assert (first["provider_max_output_tokens"], second["provider_max_output_tokens"]) == (600, 400)
    assert (first["provider_prompt_reserve_multiplier"], second["provider_prompt_reserve_multiplier"]) == (2.0, 1.0)


def test_provider_client_disables_sdk_retries(monkeypatch) -> None:
    monkeypatch.setattr(runner, "ChatOpenAI", lambda **kwargs: kwargs)
    client = runner._model.__wrapped__()
    assert client["model"] == "deepseek-flash"
    assert client["max_retries"] == 0


def test_invalid_patch_never_reaches_grader(tmp_path, monkeypatch) -> None:
    def forbidden_grade(*_args, **_kwargs):
        raise AssertionError("grader must not run for invalid model output")

    monkeypatch.setattr(runner, "grade", forbidden_grade)
    result, failure = runner._attempt(
        "public-task", tmp_path, "not json", {"excerpts": [{"path": "source.py"}]},
        "first", tmp_path,
    )
    assert not result["resolved"]
    assert failure.startswith("patch_failure:JSONDecodeError")
    assert (tmp_path / "response.first.txt").read_text(encoding="utf-8") == "not json"


def test_run_fails_closed_before_model_when_preflight_not_ready(monkeypatch) -> None:
    monkeypatch.setattr(runner, "preflight", lambda: {"ready": False})
    monkeypatch.setattr(runner, "_task", lambda _row: pytest.fail("must not invoke model"))
    with pytest.raises(RuntimeError, match="preflight not ready"):
        asyncio.run(runner.run())
