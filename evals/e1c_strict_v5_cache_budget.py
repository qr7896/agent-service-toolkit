"""Diagnostic-only remaining-byte budget thresholds from exact cache accounting."""

from __future__ import annotations

import json
import math
from pathlib import Path

from evals.e1c_admission import ROOT

CACHE = ROOT / "data" / "e1c_strict_v5_cache_accounting.json"
OUT = ROOT / "data" / "e1c_strict_v5_cache_budget.json"


def build(
    output: Path = OUT,
    cache_path: Path = CACHE,
    pull_timeout: int = 900,
) -> dict:
    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    rows = []
    for row in payload.get("rows", []):
        remaining = row.get("remaining_compressed_bytes")
        required_bps = (
            math.ceil(remaining / pull_timeout)
            if isinstance(remaining, int) and remaining >= 0 and pull_timeout > 0
            else None
        )
        rows.append(
            {
                "instance_id": row.get("instance_id"),
                "cache_accounting_ready": row.get("ready"),
                "remaining_compressed_bytes": remaining,
                "required_bytes_per_second_for_budget": required_bps,
                "required_megabytes_per_second_for_budget": round(
                    required_bps / 1_000_000, 3
                )
                if required_bps is not None
                else None,
            }
        )
    numeric = [
        row["required_bytes_per_second_for_budget"]
        for row in rows
        if isinstance(row["required_bytes_per_second_for_budget"], int)
    ]
    result = {
        "schema": "e1c-strict-v5-cache-budget-v1",
        "diagnostic_only": True,
        "changes_admission_gate": False,
        "pull_timeout_seconds": pull_timeout,
        "required_count": len(rows),
        "ready_count": sum(row["cache_accounting_ready"] is True for row in rows),
        "minimum_required_bytes_per_second_for_all_missing_images": max(numeric)
        if numeric
        else None,
        "minimum_required_megabytes_per_second_for_all_missing_images": round(
            max(numeric) / 1_000_000, 3
        )
        if numeric
        else None,
        "provider_calls": 0,
        "live_model_run": False,
        "c5_allowed": False,
        "fresh30_allowed": False,
        "rows": rows,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pull-timeout", type=int, default=900)
    args = parser.parse_args()
    print(json.dumps(build(pull_timeout=args.pull_timeout), indent=2))
