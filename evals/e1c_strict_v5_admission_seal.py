"""Seal strict-v5 pre-live admission without consuming model calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_admission_report import OUT as REPORT
from evals.e1c_strict_v5_admission_report import build

OUT = ROOT / "data" / "e1c_strict_v5_admission_seal.json"


def seal(output: Path = OUT) -> dict:
    report = build()
    evidence = report.get("evidence_rows", [])
    no_reproducer_count = sum(
        row.get("probe_status") == "no_reproducer"
        for row in evidence
        if isinstance(row, dict)
    )
    checks = report.get("checks", {}) if isinstance(report.get("checks"), dict) else {}
    prerequisites_complete = all(
        checks.get(name) is True
        for name in (
            "identity_frozen",
            "projection_supported",
            "source_identity",
            "official_image",
            "base_fail",
            "gold_pass",
            "leakage_free",
            "infrastructure_ok",
        )
    )
    decisive_failure = prerequisites_complete and no_reproducer_count > 1
    live_allowed = bool(report.get("ready")) and not decisive_failure
    value = {
        "schema": "e1c-strict-v5-prelive-admission-seal-v1",
        "provider_calls": 0,
        "live_model_run": False,
        "frozen_instance_ids": report.get("frozen_instance_ids", []),
        "admission_ready": bool(report.get("ready")),
        "trusted_reproducer_count": int(report.get("trusted_reproducer_count", 0)),
        "minimum_trusted_reproducers": int(report.get("minimum_trusted_reproducers", 2)),
        "no_reproducer_count": no_reproducer_count,
        "admission_prerequisites_complete": prerequisites_complete,
        "decisive_pre_live_failure": decisive_failure,
        "live_allowed": live_allowed,
        "decision": (
            "ready_for_exact_live_authorization"
            if live_allowed
            else "seal_without_live_run"
        ),
        "reason": (
            "trusted_reproducer_minimum_unreachable_on_frozen_canary"
            if decisive_failure
            else "admission_prerequisites_incomplete"
            if not prerequisites_complete
            else report.get("reason", "strict_v5_admission_incomplete")
        ),
        "outcome_conditioned_replacement_allowed": False,
        "same_canary_reuse_for_mechanism_tuning_allowed": False,
        "next_mechanism_must_use_new_independent_canary": not live_allowed,
        "admission_report_sha256": hashlib.sha256(REPORT.read_bytes()).hexdigest(),
    }
    value["seal_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


if __name__ == "__main__":
    print(json.dumps(seal(), ensure_ascii=False, indent=2))
