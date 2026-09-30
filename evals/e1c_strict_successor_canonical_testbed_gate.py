"""Deterministic development gate for canonical testbed interpreter successor."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable


def evaluate(
    analysis: dict,
    environment_probe: dict,
    preflights: Iterable[dict],
    *,
    prior_efil_gate: dict,
    task_specific_rule_count: int = 0,
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
    probes = list(environment_probe.get("probes", []))
    requirements = {
        "provider_calls_zero": int(analysis.get("provider_calls", 0)) == 0
        and all(int(p.get("provider_calls", 0)) == 0 for p in preflights),
        "full_dev30_denominator": int(analysis.get("task_count", 0)) == 30,
        "task_specific_rules_zero": int(task_specific_rule_count) == 0,
        "focused_tests_passed": bool(focused_tests_passed),
        "leakage_forbidden_hits_zero": int(leakage_forbidden_hits) == 0,
        "compile_ready_candidates_ge_2": int(analysis.get("compile_ready_candidate_count", 0)) >= 2,
        "compile_ready_repos_ge_2": int(analysis.get("compile_ready_repo_count", 0)) >= 2,
        "canonical_interpreter_images_ge_2": len(probes) >= 2,
        "canonical_interpreter_repos_ge_2": int(environment_probe.get("repo_count", 0)) >= 2,
        "all_environment_probes_available": bool(probes) and all(p.get("available") is True for p in probes),
        "trusted_reproducer_gain": len(trusted) >= 1,
        "prior_efil_remains_negative": prior_efil_gate.get("gate_passed") is False,
    }
    value = {
        "schema": "e1c-strict-successor-cti-development-gate-v1",
        "provider_calls": 0,
        "task_count": int(analysis.get("task_count", 0)),
        "environment_probe_count": len(probes),
        "environment_probe_repo_count": int(environment_probe.get("repo_count", 0)),
        "trusted_reproducer_count": len(trusted),
        "requirements": requirements,
        "gate_passed": all(requirements.values()),
    }
    value["gate_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value
