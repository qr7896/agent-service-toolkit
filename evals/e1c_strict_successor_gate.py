"""Deterministic zero-provider development gate for the strict successor."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable


def _sha(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def evaluate(replay: dict, preflights: Iterable[dict], *, leakage_forbidden_hits: int) -> dict:
    rows = list(replay.get("rows", []))
    preflights = list(preflights)
    provider_calls = int(replay.get("provider_calls", 0)) + sum(int(x.get("provider_calls", 0)) for x in preflights)
    consensus_tasks = int(replay.get("consensus_candidate_task_count", 0))
    minimum_support = int(replay.get("minimum_consensus_family_support_per_task", 0))
    total_support = int(replay.get("total_consensus_family_support", 0))
    promoted = [x for x in preflights if bool(x.get("execution_ready"))]
    promoted_valid = []
    for x in promoted:
        complete = all(
            [
                x.get("schema") == "e1c-strict-successor-scenario-preflight-v1",
                bool(x.get("exact_base_identity")),
                bool(x.get("immutable_image_identity")),
                bool(x.get("network_disabled")),
                bool(x.get("executed")),
                x.get("returncode") == 0,
                x.get("observable") == "scenario_exit_code == 0",
                bool(x.get("expected_base_commit")),
                x.get("expected_base_commit") == x.get("observed_base_commit"),
                isinstance(x.get("command"), list) and len(x.get("command")) > 0,
                len(str(x.get("stdout_sha256", ""))) == 64,
                len(str(x.get("stderr_sha256", ""))) == 64,
            ]
        )
        if complete:
            promoted_valid.append(x)
    reasons = {
        "provider_calls_zero": provider_calls == 0,
        "consensus_coverage_6_of_6": consensus_tasks == 6 and len(rows) == 6,
        "minimum_family_support_ge_2": minimum_support >= 2,
        "total_family_support_ge_17": total_support >= 17,
        "execution_preflighted_behavioral_gain": len(promoted_valid) > 0,
        "leakage_forbidden_hits_zero": int(leakage_forbidden_hits) == 0,
        "all_promotions_have_complete_provenance": len(promoted) == len(promoted_valid),
    }
    value = {
        "schema": "e1c-strict-successor-development-gate-v1",
        "provider_calls": provider_calls,
        "task_count": len(rows),
        "consensus_candidate_task_count": consensus_tasks,
        "minimum_consensus_family_support_per_task": minimum_support,
        "total_consensus_family_support": total_support,
        "promoted_preflight_count": len(promoted),
        "valid_promoted_preflight_count": len(promoted_valid),
        "leakage_forbidden_hits": int(leakage_forbidden_hits),
        "requirements": reasons,
        "gate_passed": all(reasons.values()),
    }
    value["gate_sha256"] = _sha(value)
    return value
