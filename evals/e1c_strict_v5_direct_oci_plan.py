"""Plan an exact official OCI acquisition without downloading image layers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_blob_preflight import (
    MANIFEST,
    _platform_manifest,
    _split_image,
    _token,
)
from evals.e1c_strict_v5_cache_accounting import _config, _local_diff_ids

OUT = ROOT / "data" / "e1c_strict_v5_direct_oci_plan.json"


def plan_image(
    image: str,
    *,
    proxy: str | None,
    timeout: int,
) -> dict:
    repository, reference = _split_image(image)
    token = _token(proxy, repository, timeout)
    manifest, manifest_meta = _platform_manifest(
        proxy,
        repository,
        reference,
        token,
        timeout,
    )
    config, config_meta = _config(
        proxy,
        repository,
        manifest,
        token,
        timeout,
    )
    local = _local_diff_ids(timeout=timeout)
    layers = manifest.get("layers", [])
    diff_ids = config.get("rootfs", {}).get("diff_ids", [])
    if len(layers) != len(diff_ids):
        raise RuntimeError("manifest_config_layer_count_mismatch")
    rows = []
    for layer, diff_id in zip(layers, diff_ids, strict=True):
        digest = layer.get("digest")
        size = layer.get("size")
        if not isinstance(digest, str) or not digest.startswith("sha256:"):
            raise RuntimeError("invalid_layer_digest")
        if not isinstance(size, int) or size < 0:
            raise RuntimeError("invalid_layer_size")
        rows.append(
            {
                "digest": digest,
                "compressed_bytes": size,
                "diff_id": diff_id,
                "cached_by_diff_id": diff_id in local,
            }
        )
    remaining = [row for row in rows if not row["cached_by_diff_id"]]
    return {
        "image": image,
        "platform_manifest_sha256": manifest_meta.get("sha256"),
        "platform_manifest_bytes": manifest_meta.get("bytes"),
        "config_sha256": config_meta.get("sha256"),
        "config_bytes": config_meta.get("bytes"),
        "layer_count": len(rows),
        "remaining_layer_count": len(remaining),
        "remaining_compressed_bytes": sum(row["compressed_bytes"] for row in remaining),
        "largest_remaining_layer_bytes": max(
            (row["compressed_bytes"] for row in remaining),
            default=0,
        ),
        "layer_plan_sha256": hashlib.sha256(
            json.dumps(rows, sort_keys=True).encode()
        ).hexdigest(),
        "rows": rows,
    }


def build(
    output: Path = OUT,
    *,
    proxy: str | None = None,
    timeout: int = 20,
    pull_timeout: int = 900,
) -> dict:
    frozen = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = []
    for task in frozen["tasks"]:
        row = plan_image(task["image"], proxy=proxy, timeout=timeout)
        row["instance_id"] = task["instance_id"]
        row["required_bytes_per_second_for_budget"] = (
            row["remaining_compressed_bytes"] + pull_timeout - 1
        ) // pull_timeout
        rows.append(row)
    result = {
        "schema": "e1c-strict-v5-direct-oci-plan-v1",
        "diagnostic_only": True,
        "changes_admission_gate": False,
        "pull_timeout_seconds": pull_timeout,
        "ready_count": len(rows),
        "required_count": len(frozen["tasks"]),
        "network_exit": {
            "explicit_proxy": bool(proxy),
            "proxy_value_recorded": False,
        },
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
    parser.add_argument("--proxy")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--pull-timeout", type=int, default=900)
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                proxy=args.proxy,
                timeout=args.timeout,
                pull_timeout=args.pull_timeout,
            ),
            indent=2,
        )
    )
