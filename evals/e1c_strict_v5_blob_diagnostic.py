"""Diagnostic-only targeted transport probe for one frozen strict-v5 image."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_blob_preflight import MANIFEST, probe_image

OUT = ROOT / "data" / "e1c_strict_v5_blob_diagnostic.json"


def run(
    instance_id: str,
    *,
    proxy: str | None = None,
    sample_bytes: int = 1024 * 1024,
    timeout: int = 30,
    min_bytes: int = 512 * 1024,
    min_bytes_per_second: int = 64 * 1024,
    max_estimated_seconds: int | None = 900,
    output: Path = OUT,
) -> dict:
    frozen = json.loads(MANIFEST.read_text(encoding="utf-8"))
    matches = [
        task for task in frozen.get("tasks", [])
        if task.get("instance_id") == instance_id
    ]
    if len(matches) != 1:
        raise ValueError("instance_id_not_in_frozen_manifest")
    task = matches[0]
    row = probe_image(
        task["image"],
        proxy=proxy,
        sample_bytes=sample_bytes,
        timeout=timeout,
        min_bytes=min_bytes,
        min_bytes_per_second=min_bytes_per_second,
        max_estimated_seconds=max_estimated_seconds,
    )
    row["instance_id"] = instance_id
    result = {
        "schema": "e1c-strict-v5-blob-diagnostic-v1",
        "diagnostic_only": True,
        "changes_admission_gate": False,
        "instance_id": instance_id,
        "ready_under_same_budget_estimate": row.get("ready") is True,
        "formal_admission_ready": False,
        "network_exit": {
            "explicit_proxy": bool(proxy),
            "proxy_value_recorded": False,
        },
        "provider_calls": 0,
        "live_model_run": False,
        "c5_allowed": False,
        "fresh30_allowed": False,
        "row": row,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance-id", required=True)
    parser.add_argument("--proxy")
    parser.add_argument("--sample-bytes", type=int, default=1024 * 1024)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--min-bytes", type=int, default=512 * 1024)
    parser.add_argument("--min-bytes-per-second", type=int, default=64 * 1024)
    parser.add_argument("--max-estimated-seconds", type=int, default=900)
    args = parser.parse_args()
    print(
        json.dumps(
            run(
                args.instance_id,
                proxy=args.proxy,
                sample_bytes=args.sample_bytes,
                timeout=args.timeout,
                min_bytes=args.min_bytes,
                min_bytes_per_second=args.min_bytes_per_second,
                max_estimated_seconds=args.max_estimated_seconds,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
