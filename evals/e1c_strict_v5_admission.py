"""Fail-closed zero-provider admission model for a frozen strict-v5 canary."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

MIN_TRUSTED_REPRODUCERS = 2


@dataclass(frozen=True)
class AdmissionRow:
    instance_id: str
    identity_frozen: bool
    projection_status: str
    source_commit_matches: bool
    image_present: bool
    base_fail: bool
    gold_pass: bool
    trusted_reproducer: bool
    leakage_free: bool
    infrastructure_ok: bool

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def evaluate(rows: list[AdmissionRow]) -> dict:
    if len(rows) != 3:
        return {
            "schema": "e1c-strict-v5-canary-admission-v1",
            "ready": False,
            "reason": "canary_identity_not_exactly_three",
            "provider_calls": 0,
            "trusted_reproducer_count": 0,
        }
    checks = {
        "identity_frozen": all(row.identity_frozen for row in rows),
        "projection_supported": all(row.projection_status == "projected" for row in rows),
        "source_identity": all(row.source_commit_matches for row in rows),
        "official_image": all(row.image_present for row in rows),
        "base_fail": all(row.base_fail for row in rows),
        "gold_pass": all(row.gold_pass for row in rows),
        "leakage_free": all(row.leakage_free for row in rows),
        "infrastructure_ok": all(row.infrastructure_ok for row in rows),
    }
    trusted = sum(row.trusted_reproducer for row in rows)
    checks["trusted_reproducer_minimum"] = trusted >= MIN_TRUSTED_REPRODUCERS
    ready = all(checks.values())
    value = {
        "schema": "e1c-strict-v5-canary-admission-v1",
        "ready": ready,
        "reason": "ready_for_live_freeze" if ready else "strict_v5_admission_incomplete",
        "provider_calls": 0,
        "trusted_reproducer_count": trusted,
        "minimum_trusted_reproducers": MIN_TRUSTED_REPRODUCERS,
        "checks": checks,
        "rows": [row.as_dict() for row in rows],
        "new_task_tree_touched": False,
    }
    value["admission_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value
