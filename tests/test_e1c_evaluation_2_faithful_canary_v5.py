import asyncio

import pytest

from evals import e1c_evaluation_2_faithful_canary_v5 as canary
from evals.e1c_evaluation_2_container_health import ContainerInfrastructureUnavailable


def test_engine_failure_prevents_request(monkeypatch):
    events = []
    monkeypatch.setattr(canary.frame.stage.materialize, "verified_image", lambda iid: "sha256:fixture")

    def unhealthy(images):
        raise ContainerInfrastructureUnavailable("fixture engine unavailable")

    async def provider(*args, **kwargs):
        events.append("request")

    monkeypatch.setattr(canary, "require_engine", unhealthy)
    monkeypatch.setattr(canary, "budgeted_ainvoke", provider)
    with pytest.raises(ContainerInfrastructureUnavailable):
        asyncio.run(canary.guarded_invoke(None, [], {"configurable": {"provider_task_id": "synthetic"}}, role="B"))
    assert events == []


def test_engine_health_precedes_request_and_preserves_config(monkeypatch):
    events = []
    config = {"configurable": {"provider_task_id": "synthetic"}}
    monkeypatch.setattr(canary.frame.stage.materialize, "verified_image", lambda iid: "sha256:fixture")
    monkeypatch.setattr(canary, "require_engine", lambda images: events.append(("health", images)))

    async def provider(model, messages, received, *, role):
        assert received is config and role == "B"
        events.append(("request", role))
        return "preserved"

    monkeypatch.setattr(canary, "budgeted_ainvoke", provider)
    assert asyncio.run(canary.guarded_invoke(None, [], config, role="B")) == "preserved"
    assert events == [("health", ("sha256:fixture",)), ("request", "B")]


def test_transitive_method_bindings_include_facts_locator_and_health():
    assert "evals/e1c_blind_boundary.py" in canary.FILES
    for name in ("issue_fixture_facts", "public_api_windows", "container_health", "faithful_dev"):
        assert any(f"/{'e1c_evaluation_2_' + name}.py" in path for path in canary.FILES)
    assert canary.IDENTITY != canary.runner.IDENTITY and canary.OUT != canary.runner.OUT
