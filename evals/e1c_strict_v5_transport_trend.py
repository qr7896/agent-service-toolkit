"""Diagnostic-only trend summary for strict-v5 bounded transport evidence."""

from __future__ import annotations

import json
from pathlib import Path

from evals.e1c_admission import ROOT

LEDGER = ROOT / "data" / "e1c_strict_v5_blob_preflight_ledger.jsonl"
OUT = ROOT / "data" / "e1c_strict_v5_transport_trend.json"


def _load_ledger(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _first_row(entry: dict) -> dict:
    rows = entry.get("rows", [])
    return rows[0] if rows else {}


def _classify(entries: list[dict], pull_timeout: int) -> dict:
    observations = [_first_row(entry) for entry in entries if entry.get("rows")]
    ready_rows = [row for row in observations if row.get("ready") is True]
    error_rows = [
        row for row in observations if row.get("reason") == "blob_preflight_error"
    ]
    budget_rows = [
        row
        for row in observations
        if isinstance(row.get("estimated_full_image_seconds"), (int, float))
    ]
    budget_compatible = [
        row
        for row in budget_rows
        if row["estimated_full_image_seconds"] <= pull_timeout
    ]
    partial_rows = [
        row
        for row in observations
        if isinstance(row.get("partial_bytes_received"), int)
        and isinstance(row.get("requested_bytes"), int)
        and row["requested_bytes"] > 0
    ]
    partial_ratios = [
        row["partial_bytes_received"] / row["requested_bytes"] for row in partial_rows
    ]

    if not observations:
        state = "no_evidence"
    elif budget_compatible:
        state = "budget_compatible_observed"
    elif len(error_rows) >= 2 and len(error_rows) == len(observations):
        state = "repeated_bounded_transport_error"
    elif budget_rows and all(
        row["estimated_full_image_seconds"] > pull_timeout for row in budget_rows
    ):
        state = "repeated_budget_incompatible"
    else:
        state = "mixed_or_insufficient"

    return {
        "state": state,
        "observation_count": len(observations),
        "ready_observation_count": len(ready_rows),
        "bounded_error_count": len(error_rows),
        "budget_estimate_count": len(budget_rows),
        "budget_compatible_observation_count": len(budget_compatible),
        "partial_progress_observation_count": len(partial_rows),
        "latest_partial_ratio": round(partial_ratios[-1], 6)
        if partial_ratios
        else None,
        "best_partial_ratio": round(max(partial_ratios), 6)
        if partial_ratios
        else None,
    }


def build(
    output: Path = OUT,
    ledger: Path = LEDGER,
    pull_timeout: int = 900,
) -> dict:
    entries = _load_ledger(ledger)
    summary = _classify(entries, pull_timeout)
    latest = _first_row(entries[-1]) if entries else {}
    result = {
        "schema": "e1c-strict-v5-transport-trend-v1",
        "diagnostic_only": True,
        "changes_admission_gate": False,
        "pull_timeout_seconds": pull_timeout,
        **summary,
        "latest_instance_id": latest.get("instance_id"),
        "latest_reason": latest.get("reason"),
        "latest_error_sha256": latest.get("error_sha256"),
        "recheck_information_gain_likely": summary["state"]
        not in {
            "repeated_bounded_transport_error",
            "repeated_budget_incompatible",
        },
        "formal_admission_source": "e1c_strict_v5_blob_preflight",
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
