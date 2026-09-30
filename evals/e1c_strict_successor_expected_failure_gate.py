"""Deterministic development gate for expected-failure/import-lift successor."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable


def evaluate(
    analysis: dict,
    preflights: Iterable[dict],
    *,
    prior_setup_closure_gate: dict,
    task_specific_rule_count: int = 0,
    forbidden_setup_access_count: int = 0,
    leakage_forbidden_hits: int = 0,
    focused_tests_passed: bool = True,
) -> dict:
    preflights = list(preflights)
    trusted = [
        p
        for p in preflights
        if p.get("trusted_reproducer") is True
        and p.get("exact_base_identity") is True
        and p.get("immutable_image_identity") is True
        and p.get("network_disabled") is True
        and p.get("executed") is True
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
        "exception_contract_candidates_ge_2": int(analysis.get("exception_contract_candidate_count", 0)) >= 2,
        "exception_contract_repos_ge_2": int(analysis.get("exception_contract_repo_count", 0)) >= 2,
        "compile_ready_candidates_ge_2": int(analysis.get("compile_ready_candidate_count", 0)) >= 2,
        "compile_ready_repos_ge_2": int(analysis.get("compile_ready_repo_count", 0)) >= 2,
        "trusted_reproducer_gain": len(trusted) >= 1,
        "prior_setup_closure_remains_negative": prior_setup_closure_gate.get("gate_passed") is False,
    }
    value = {
        "schema": "e1c-strict-successor-expected-failure-development-gate-v1",
        "provider_calls": provider_calls,
        "task_count": int(analysis.get("task_count", 0)),
        "exception_contract_candidate_count": int(analysis.get("exception_contract_candidate_count", 0)),
        "exception_contract_repo_count": int(analysis.get("exception_contract_repo_count", 0)),
        "compile_ready_candidate_count": int(analysis.get("compile_ready_candidate_count", 0)),
        "compile_ready_repo_count": int(analysis.get("compile_ready_repo_count", 0)),
        "trusted_reproducer_count": len(trusted),
        "requirements": requirements,
        "gate_passed": all(requirements.values()),
    }
    value["gate_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value
