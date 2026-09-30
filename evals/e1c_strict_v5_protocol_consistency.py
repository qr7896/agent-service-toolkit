"""Fail-closed pre-live consistency audit across strict-v5 gate artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_gate import c5_gate, canary_gate, fresh30_gate
from evals.e1c_strict_v5_legacy_artifact_seal import OUT as LEGACY_SEAL
from evals.e1c_strict_v5_legacy_artifact_seal import verify as verify_legacy
from evals.e1c_strict_v5_workspace_snapshot import OUT as WORKSPACE_SNAPSHOT
from evals.e1c_strict_v5_workspace_snapshot import verify as verify_workspace

SEAL = ROOT / "data" / "e1c_strict_v5_admission_seal.json"
INFRA = ROOT / "data" / "e1c_strict_v5_infra_gate.json"
TREND = ROOT / "data" / "e1c_strict_v5_transport_trend.json"
CACHE_BUDGET = ROOT / "data" / "e1c_strict_v5_cache_budget.json"
ENGINEERING = ROOT / "data" / "e1c_strict_v5_engineering_readiness.json"
OUT = ROOT / "data" / "e1c_strict_v5_protocol_consistency.json"


def _read(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build(output: Path = OUT) -> dict:
    seal = _read(SEAL)
    infra = _read(INFRA)
    trend = _read(TREND)
    cache = _read(CACHE_BUDGET)
    engineering = _read(ENGINEERING)
    legacy_seal = _read(LEGACY_SEAL)
    legacy_verification = (
        verify_legacy(LEGACY_SEAL) if legacy_seal is not None else None
    )
    workspace_snapshot = _read(WORKSPACE_SNAPSHOT)
    workspace_verification = (
        verify_workspace(WORKSPACE_SNAPSHOT)
        if workspace_snapshot is not None
        else None
    )
    canary = canary_gate()
    c5 = c5_gate()
    fresh = fresh30_gate()

    missing = [
        name
        for name, value in {
            "admission_seal": seal,
            "infra_gate": infra,
            "transport_trend": trend,
            "cache_budget": cache,
            "engineering_readiness": engineering,
            "legacy_artifact_seal": legacy_seal,
            "workspace_snapshot": workspace_snapshot,
        }.items()
        if value is None
    ]
    checks = {
        "artifacts_present": not missing,
        "prelive_seal_closed": bool(seal) and seal.get("live_allowed") is False,
        "canary_gate_closed": canary.get("ready") is False,
        "c5_gate_closed": c5.get("ready") is False,
        "fresh30_gate_closed": fresh.get("ready") is False,
        "fresh30_materialization_closed": fresh.get("materialization_allowed") is False,
        "infra_c5_closed": bool(infra) and infra.get("c5_allowed") is False,
        "infra_fresh30_closed": bool(infra) and infra.get("fresh30_allowed") is False,
        "trend_diagnostic_only": bool(trend)
        and trend.get("diagnostic_only") is True
        and trend.get("changes_admission_gate") is False,
        "trend_c5_closed": bool(trend) and trend.get("c5_allowed") is False,
        "trend_fresh30_closed": bool(trend) and trend.get("fresh30_allowed") is False,
        "cache_diagnostic_only": bool(cache)
        and cache.get("diagnostic_only") is True
        and cache.get("changes_admission_gate") is False,
        "cache_c5_closed": bool(cache) and cache.get("c5_allowed") is False,
        "cache_fresh30_closed": bool(cache) and cache.get("fresh30_allowed") is False,
        "engineering_a_through_e_ready": bool(engineering)
        and engineering.get("engineering_ready_a_through_e") is True,
        "engineering_live_closed": bool(engineering)
        and engineering.get("live_allowed") is False,
        "engineering_c5_closed": bool(engineering)
        and engineering.get("c5_allowed") is False,
        "engineering_fresh30_closed": bool(engineering)
        and engineering.get("fresh30_allowed") is False,
        "engineering_canary_admission_closed": bool(engineering)
        and engineering.get("independent_canary_admission_ready") is False,
        "legacy_artifacts_unchanged": bool(legacy_verification)
        and legacy_verification.get("match") is True,
        "legacy_results_not_authoritative_for_v5": bool(legacy_seal)
        and legacy_seal.get("legacy_results_authoritative_for_v5") is False,
        "workspace_snapshot_current": bool(workspace_verification)
        and workspace_verification.get("match") is True,
        "workspace_head_not_misrepresented": bool(workspace_snapshot)
        and (
            workspace_snapshot.get("head_is_sufficient_identity") is True
            or workspace_snapshot.get("workspace_identity_required") is True
        ),
        "new_task_tree_untouched": fresh.get("new_task_tree_touched") is False,
    }
    provider_call_values = [
        value.get("provider_calls")
        for value in (seal, infra, trend, cache, engineering)
        if isinstance(value, dict) and "provider_calls" in value
    ]
    checks["zero_provider_calls_in_audited_artifacts"] = all(
        value == 0 for value in provider_call_values
    )
    consistent = all(checks.values())
    result = {
        "schema": "e1c-strict-v5-prelive-protocol-consistency-v1",
        "consistent": consistent,
        "reason": (
            "strict_v5_prelive_lineage_consistent"
            if consistent
            else "strict_v5_prelive_lineage_inconsistent"
        ),
        "missing_artifacts": missing,
        "checks": checks,
        "canary_gate_reason": canary.get("reason"),
        "c5_gate_reason": c5.get("reason"),
        "fresh30_gate_reason": fresh.get("reason"),
        "engineering_readiness_reason": (
            engineering.get("reason") if isinstance(engineering, dict) else None
        ),
        "legacy_artifact_seal_sha256": (
            legacy_seal.get("seal_sha256")
            if isinstance(legacy_seal, dict)
            else None
        ),
        "legacy_artifact_seal_match": (
            legacy_verification.get("match")
            if isinstance(legacy_verification, dict)
            else False
        ),
        "workspace_identity_sha256": (
            workspace_snapshot.get("identity_sha256")
            if isinstance(workspace_snapshot, dict)
            else None
        ),
        "workspace_snapshot_match": (
            workspace_verification.get("match")
            if isinstance(workspace_verification, dict)
            else False
        ),
        "provider_calls": 0,
        "live_model_run": False,
        "new_task_tree_touched": fresh.get("new_task_tree_touched", False),
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
