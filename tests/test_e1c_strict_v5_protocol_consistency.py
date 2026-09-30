import json

import pytest

import evals.e1c_strict_v5_protocol_consistency as audit


def _write(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


@pytest.fixture(autouse=True)
def _workspace_snapshot_current(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace.json"
    _write(
        workspace,
        {
            "identity_sha256": "a" * 64,
            "head_is_sufficient_identity": False,
            "workspace_identity_required": True,
        },
    )
    monkeypatch.setattr(audit, "WORKSPACE_SNAPSHOT", workspace)
    monkeypatch.setattr(audit, "verify_workspace", lambda path: {"match": True})
    legacy = tmp_path / "legacy.json"
    _write(
        legacy,
        {
            "seal_sha256": "b" * 64,
            "legacy_results_authoritative_for_v5": False,
        },
    )
    monkeypatch.setattr(audit, "LEGACY_SEAL", legacy)
    monkeypatch.setattr(audit, "verify_legacy", lambda path: {"match": True})
    engineering = tmp_path / "engineering.json"
    _write(
        engineering,
        {
            "engineering_ready_a_through_e": True,
            "independent_canary_admission_ready": False,
            "provider_calls": 0,
            "live_allowed": False,
            "c5_allowed": False,
            "fresh30_allowed": False,
            "reason": "engineering_ready",
        },
    )
    monkeypatch.setattr(audit, "ENGINEERING", engineering)


def test_consistency_passes_only_when_every_downstream_gate_is_closed(
    tmp_path, monkeypatch
) -> None:
    seal = tmp_path / "seal.json"
    infra = tmp_path / "infra.json"
    trend = tmp_path / "trend.json"
    cache = tmp_path / "cache.json"
    _write(seal, {"live_allowed": False, "provider_calls": 0})
    _write(
        infra,
        {"c5_allowed": False, "fresh30_allowed": False, "provider_calls": 0},
    )
    _write(
        trend,
        {
            "diagnostic_only": True,
            "changes_admission_gate": False,
            "c5_allowed": False,
            "fresh30_allowed": False,
            "provider_calls": 0,
        },
    )
    _write(
        cache,
        {
            "diagnostic_only": True,
            "changes_admission_gate": False,
            "c5_allowed": False,
            "fresh30_allowed": False,
            "provider_calls": 0,
        },
    )
    monkeypatch.setattr(audit, "SEAL", seal)
    monkeypatch.setattr(audit, "INFRA", infra)
    monkeypatch.setattr(audit, "TREND", trend)
    monkeypatch.setattr(audit, "CACHE_BUDGET", cache)
    monkeypatch.setattr(
        audit,
        "canary_gate",
        lambda: {"ready": False, "reason": "canary_closed"},
    )
    monkeypatch.setattr(
        audit,
        "c5_gate",
        lambda: {"ready": False, "reason": "c5_closed"},
    )
    monkeypatch.setattr(
        audit,
        "fresh30_gate",
        lambda: {
            "ready": False,
            "reason": "fresh_closed",
            "materialization_allowed": False,
            "new_task_tree_touched": False,
        },
    )
    result = audit.build(output=tmp_path / "out.json")
    assert result["consistent"] is True
    assert all(result["checks"].values())


def test_consistency_fails_if_advisory_artifact_claims_c5_open(
    tmp_path, monkeypatch
) -> None:
    seal = tmp_path / "seal.json"
    infra = tmp_path / "infra.json"
    trend = tmp_path / "trend.json"
    cache = tmp_path / "cache.json"
    _write(seal, {"live_allowed": False, "provider_calls": 0})
    _write(
        infra,
        {"c5_allowed": False, "fresh30_allowed": False, "provider_calls": 0},
    )
    _write(
        trend,
        {
            "diagnostic_only": True,
            "changes_admission_gate": False,
            "c5_allowed": True,
            "fresh30_allowed": False,
            "provider_calls": 0,
        },
    )
    _write(
        cache,
        {
            "diagnostic_only": True,
            "changes_admission_gate": False,
            "c5_allowed": False,
            "fresh30_allowed": False,
            "provider_calls": 0,
        },
    )
    monkeypatch.setattr(audit, "SEAL", seal)
    monkeypatch.setattr(audit, "INFRA", infra)
    monkeypatch.setattr(audit, "TREND", trend)
    monkeypatch.setattr(audit, "CACHE_BUDGET", cache)
    monkeypatch.setattr(audit, "canary_gate", lambda: {"ready": False})
    monkeypatch.setattr(audit, "c5_gate", lambda: {"ready": False})
    monkeypatch.setattr(
        audit,
        "fresh30_gate",
        lambda: {
            "ready": False,
            "materialization_allowed": False,
            "new_task_tree_touched": False,
        },
    )
    result = audit.build(output=tmp_path / "out.json")
    assert result["consistent"] is False
    assert result["checks"]["trend_c5_closed"] is False


def test_consistency_fails_closed_when_required_artifact_missing(
    tmp_path, monkeypatch
) -> None:
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(audit, "SEAL", missing)
    monkeypatch.setattr(audit, "INFRA", missing)
    monkeypatch.setattr(audit, "TREND", missing)
    monkeypatch.setattr(audit, "CACHE_BUDGET", missing)
    monkeypatch.setattr(audit, "ENGINEERING", missing)
    monkeypatch.setattr(audit, "LEGACY_SEAL", missing)
    monkeypatch.setattr(audit, "WORKSPACE_SNAPSHOT", missing)
    monkeypatch.setattr(audit, "canary_gate", lambda: {"ready": False})
    monkeypatch.setattr(audit, "c5_gate", lambda: {"ready": False})
    monkeypatch.setattr(
        audit,
        "fresh30_gate",
        lambda: {
            "ready": False,
            "materialization_allowed": False,
            "new_task_tree_touched": False,
        },
    )
    result = audit.build(output=tmp_path / "out.json")
    assert result["consistent"] is False
    assert result["checks"]["artifacts_present"] is False
    assert len(result["missing_artifacts"]) == 7


def test_consistency_fails_if_workspace_snapshot_has_drift(
    tmp_path, monkeypatch
) -> None:
    seal = tmp_path / "seal.json"
    infra = tmp_path / "infra.json"
    trend = tmp_path / "trend.json"
    cache = tmp_path / "cache.json"
    _write(seal, {"live_allowed": False, "provider_calls": 0})
    _write(
        infra,
        {"c5_allowed": False, "fresh30_allowed": False, "provider_calls": 0},
    )
    advisory = {
        "diagnostic_only": True,
        "changes_admission_gate": False,
        "c5_allowed": False,
        "fresh30_allowed": False,
        "provider_calls": 0,
    }
    _write(trend, advisory)
    _write(cache, advisory)
    monkeypatch.setattr(audit, "SEAL", seal)
    monkeypatch.setattr(audit, "INFRA", infra)
    monkeypatch.setattr(audit, "TREND", trend)
    monkeypatch.setattr(audit, "CACHE_BUDGET", cache)
    monkeypatch.setattr(audit, "verify_workspace", lambda path: {"match": False})
    monkeypatch.setattr(audit, "canary_gate", lambda: {"ready": False})
    monkeypatch.setattr(audit, "c5_gate", lambda: {"ready": False})
    monkeypatch.setattr(
        audit,
        "fresh30_gate",
        lambda: {
            "ready": False,
            "materialization_allowed": False,
            "new_task_tree_touched": False,
        },
    )
    result = audit.build(output=tmp_path / "out.json")
    assert result["consistent"] is False
    assert result["checks"]["workspace_snapshot_current"] is False


def test_consistency_fails_if_legacy_artifact_seal_drifted(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(audit, "verify_legacy", lambda path: {"match": False})
    monkeypatch.setattr(audit, "canary_gate", lambda: {"ready": False})
    monkeypatch.setattr(audit, "c5_gate", lambda: {"ready": False})
    monkeypatch.setattr(
        audit,
        "fresh30_gate",
        lambda: {
            "ready": False,
            "materialization_allowed": False,
            "new_task_tree_touched": False,
        },
    )
    seal = tmp_path / "seal.json"
    infra = tmp_path / "infra.json"
    trend = tmp_path / "trend.json"
    cache = tmp_path / "cache.json"
    _write(seal, {"live_allowed": False, "provider_calls": 0})
    _write(
        infra,
        {"c5_allowed": False, "fresh30_allowed": False, "provider_calls": 0},
    )
    advisory = {
        "diagnostic_only": True,
        "changes_admission_gate": False,
        "c5_allowed": False,
        "fresh30_allowed": False,
        "provider_calls": 0,
    }
    _write(trend, advisory)
    _write(cache, advisory)
    monkeypatch.setattr(audit, "SEAL", seal)
    monkeypatch.setattr(audit, "INFRA", infra)
    monkeypatch.setattr(audit, "TREND", trend)
    monkeypatch.setattr(audit, "CACHE_BUDGET", cache)
    result = audit.build(output=tmp_path / "out.json")
    assert result["consistent"] is False
    assert result["checks"]["legacy_artifacts_unchanged"] is False


def test_consistency_fails_if_engineering_readiness_opens_live(
    tmp_path, monkeypatch
) -> None:
    engineering = tmp_path / "engineering.json"
    _write(
        engineering,
        {
            "engineering_ready_a_through_e": True,
            "independent_canary_admission_ready": False,
            "provider_calls": 0,
            "live_allowed": True,
            "c5_allowed": False,
            "fresh30_allowed": False,
        },
    )
    monkeypatch.setattr(audit, "ENGINEERING", engineering)
    monkeypatch.setattr(audit, "canary_gate", lambda: {"ready": False})
    monkeypatch.setattr(audit, "c5_gate", lambda: {"ready": False})
    monkeypatch.setattr(
        audit,
        "fresh30_gate",
        lambda: {
            "ready": False,
            "materialization_allowed": False,
            "new_task_tree_touched": False,
        },
    )
    seal = tmp_path / "seal.json"
    infra = tmp_path / "infra.json"
    trend = tmp_path / "trend.json"
    cache = tmp_path / "cache.json"
    _write(seal, {"live_allowed": False, "provider_calls": 0})
    _write(
        infra,
        {"c5_allowed": False, "fresh30_allowed": False, "provider_calls": 0},
    )
    advisory = {
        "diagnostic_only": True,
        "changes_admission_gate": False,
        "c5_allowed": False,
        "fresh30_allowed": False,
        "provider_calls": 0,
    }
    _write(trend, advisory)
    _write(cache, advisory)
    monkeypatch.setattr(audit, "SEAL", seal)
    monkeypatch.setattr(audit, "INFRA", infra)
    monkeypatch.setattr(audit, "TREND", trend)
    monkeypatch.setattr(audit, "CACHE_BUDGET", cache)
    result = audit.build(output=tmp_path / "out.json")
    assert result["consistent"] is False
    assert result["checks"]["engineering_live_closed"] is False
