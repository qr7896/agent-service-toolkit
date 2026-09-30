"""Read-only infrastructure decision gate for frozen strict-v5 admission."""

from __future__ import annotations

import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_resume_admission import inspect_local_images

IDENTITY = ROOT / "data" / "e1c_strict_v5_image_identity.json"
BLOB_PREFLIGHT = ROOT / "data" / "e1c_strict_v5_blob_preflight.json"
TRANSPORT_TREND = ROOT / "data" / "e1c_strict_v5_transport_trend.json"
CACHE_BUDGET = ROOT / "data" / "e1c_strict_v5_cache_budget.json"
OUT = ROOT / "data" / "e1c_strict_v5_infra_gate.json"


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build(output: Path = OUT, pull_timeout: int = 900) -> dict:
    local = inspect_local_images()
    identity = _read_json(IDENTITY)
    transport = _read_json(BLOB_PREFLIGHT)
    trend = _read_json(TRANSPORT_TREND)
    cache_budget = _read_json(CACHE_BUDGET)
    identity_rows = identity.get("rows", [])
    mismatch_rows = [
        row["instance_id"]
        for row in identity_rows
        if row.get("authoritative_digest")
        and row.get("mirror_digest")
        and row.get("authoritative_digest") != row.get("mirror_digest")
    ]
    mirror_closed = bool(mismatch_rows)
    local_ready = bool(local.get("ready"))
    transport_ready = bool(transport.get("ready"))
    acquisition_allowed = local_ready or transport_ready

    if local_ready:
        reason = "frozen_official_images_local"
        next_action = "resume_admission"
    elif transport_ready:
        reason = "official_acquisition_budget_admissible"
        next_action = "advance_admission"
    else:
        reason = "official_transport_not_budget_admissible"
        next_action = "bounded_transport_preflight_only"

    result = {
        "schema": "e1c-strict-v5-infra-gate-v1",
        "ready": local_ready,
        "reason": reason,
        "next_action": next_action,
        "pull_timeout_seconds": pull_timeout,
        "full_pull_allowed": acquisition_allowed and not local_ready,
        "local_official_images_ready": local_ready,
        "missing_instance_ids": local.get("missing_instance_ids", []),
        "latest_blob_preflight_ready": transport_ready,
        "latest_blob_preflight_reason": transport.get("reason"),
        "latest_blob_checked_count": transport.get("checked_count", 0),
        "transport_trend_state": trend.get("state"),
        "transport_recheck_information_gain_likely": trend.get(
            "recheck_information_gain_likely"
        ),
        "transport_trend_diagnostic_only": trend.get("diagnostic_only"),
        "transport_trend_changes_admission_gate": trend.get(
            "changes_admission_gate"
        ),
        "cache_budget_diagnostic_only": cache_budget.get("diagnostic_only"),
        "cache_budget_changes_admission_gate": cache_budget.get(
            "changes_admission_gate"
        ),
        "cache_budget_minimum_required_bytes_per_second": cache_budget.get(
            "minimum_required_bytes_per_second_for_all_missing_images"
        ),
        "cache_budget_minimum_required_megabytes_per_second": cache_budget.get(
            "minimum_required_megabytes_per_second_for_all_missing_images"
        ),
        "authoritative_ready_count": identity.get("authoritative_ready_count", 0),
        "mirror_equivalent_count": identity.get("mirror_equivalent_count", 0),
        "mirror_mismatch_count": len(mismatch_rows),
        "mirror_mismatch_instance_ids": mismatch_rows,
        "mirror_route_conclusively_closed": mirror_closed,
        "mirror_pull_allowed": bool(identity.get("mirror_transport_ready"))
        and not mirror_closed,
        "provider_calls": 0,
        "live_model_run": False,
        "c5_allowed": False,
        "fresh30_allowed": False,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pull-timeout", type=int, default=900)
    args = parser.parse_args()
    print(json.dumps(build(pull_timeout=args.pull_timeout), indent=2))
