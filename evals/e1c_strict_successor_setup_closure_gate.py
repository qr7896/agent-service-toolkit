"""Deterministic development gate for the strict setup-closure successor."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable


def _sha(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def evaluate(
    analysis: dict,
    preflights: Iterable[dict],
    *,
    django11734_preflight: dict,
    v25_replay: dict,
    task_specific_rule_count: int = 0,
    forbidden_setup_access_count: int = 0,
    leakage_forbidden_hits: int = 0,
    focused_tests_passed: bool = True,
) -> dict:
    preflights = list(preflights)
    valid_promotions = [
        p
        for p in preflights
        if p.get("execution_ready") is True
        and p.get("exact_base_identity") is True
        and p.get("immutable_image_identity") is True
        and p.get("network_disabled") is True
        and p.get("executed") is True
        and p.get("returncode") == 0
        and p.get("observable") == "scenario_exit_code == 0"
        and p.get("expected_base_commit") == p.get("observed_base_commit")
        and int(p.get("provider_calls", 0)) == 0
    ]
    provider_calls = int(analysis.get("provider_calls", 0)) + sum(
        int(p.get("provider_calls", 0)) for p in preflights
    )
    requirements = {
        "provider_calls_zero": provider_calls == 0,
        "full_dev30_denominator": int(analysis.get("task_count", 0)) == 30,
        "task_specific_rules_zero": int(task_specific_rule_count) == 0,
        "forbidden_setup_access_zero": int(forbidden_setup_access_count) == 0,
        "focused_tests_passed": bool(focused_tests_passed),
        "leakage_forbidden_hits_zero": int(leakage_forbidden_hits) == 0,
        "behavioral_candidate_count_ge_3": int(analysis.get("behavioral_closed_candidate_count", 0)) >= 3,
        "behavioral_candidate_repo_count_ge_2": int(analysis.get("behavioral_closed_repo_count", 0)) >= 2,
        "real_execution_preflight_gain": len(valid_promotions) >= 1,
        "django11734_remains_fail_closed": django11734_preflight.get("execution_ready") is False,
        "v25_consensus_6_of_6": int(v25_replay.get("consensus_candidate_task_count", 0)) == 6,
        "v25_minimum_family_support_ge_2": int(v25_replay.get("minimum_consensus_family_support_per_task", 0)) >= 2,
        "v25_total_family_support_ge_17": int(v25_replay.get("total_consensus_family_support", 0)) >= 17,
    }
    value = {
        "schema": "e1c-strict-successor-setup-closure-development-gate-v1",
        "provider_calls": provider_calls,
        "task_count": int(analysis.get("task_count", 0)),
        "behavioral_closed_candidate_count": int(analysis.get("behavioral_closed_candidate_count", 0)),
        "behavioral_closed_repo_count": int(analysis.get("behavioral_closed_repo_count", 0)),
        "valid_promoted_preflight_count": len(valid_promotions),
        "requirements": requirements,
        "gate_passed": all(requirements.values()),
    }
    value["gate_sha256"] = _sha(value)
    return value
