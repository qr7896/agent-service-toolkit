"""Diagnostic-only exact layer-cache accounting for frozen strict-v5 images."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_blob_preflight import (
    REGISTRY,
    _json_get,
    _platform_manifest,
    _split_image,
    _token,
)

MANIFEST = ROOT / "data" / "e1c_strict_v5_canary_manifest.json"
OUT = ROOT / "data" / "e1c_strict_v5_cache_accounting.json"


def _local_diff_ids(timeout: int = 30) -> set[str]:
    listed = subprocess.run(
        ["docker", "image", "ls", "-q", "--no-trunc"],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if listed.returncode != 0:
        raise RuntimeError("docker_image_list_failed")
    image_ids = sorted(set(line.strip() for line in listed.stdout.splitlines() if line.strip()))
    if not image_ids:
        return set()
    inspected = subprocess.run(
        ["docker", "image", "inspect", *image_ids],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if inspected.returncode != 0:
        raise RuntimeError("docker_image_inspect_failed")
    payload = json.loads(inspected.stdout)
    return {
        layer
        for image in payload
        for layer in image.get("RootFS", {}).get("Layers", [])
        if isinstance(layer, str) and layer.startswith("sha256:")
    }


def _config(
    proxy: str | None,
    repository: str,
    manifest: dict,
    token: str,
    timeout: int,
) -> tuple[dict, dict]:
    descriptor = manifest.get("config", {})
    digest = descriptor.get("digest")
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        raise RuntimeError("config_digest_invalid")
    return _json_get(
        proxy,
        f"{REGISTRY}/v2/{repository}/blobs/{digest}",
        {"Authorization": f"Bearer {token}", "Accept-Encoding": "identity"},
        timeout,
    )


def _account(
    manifest: dict,
    config: dict,
    local_diff_ids: set[str],
) -> dict:
    layers = manifest.get("layers", [])
    diff_ids = config.get("rootfs", {}).get("diff_ids", [])
    if len(layers) != len(diff_ids):
        raise RuntimeError("manifest_config_layer_count_mismatch")
    paired = []
    for layer, diff_id in zip(layers, diff_ids, strict=True):
        size = layer.get("size")
        digest = layer.get("digest")
        if (
            not isinstance(size, int)
            or size < 0
            or not isinstance(digest, str)
            or not digest.startswith("sha256:")
            or not isinstance(diff_id, str)
            or not diff_id.startswith("sha256:")
        ):
            raise RuntimeError("invalid_layer_descriptor")
        paired.append(
            {
                "compressed_digest": digest,
                "diff_id": diff_id,
                "compressed_bytes": size,
                "cached_by_diff_id": diff_id in local_diff_ids,
            }
        )
    total = sum(row["compressed_bytes"] for row in paired)
    cached = sum(
        row["compressed_bytes"] for row in paired if row["cached_by_diff_id"]
    )
    remaining = total - cached
    return {
        "layer_count": len(paired),
        "cached_layer_count": sum(row["cached_by_diff_id"] for row in paired),
        "total_compressed_bytes": total,
        "cached_compressed_bytes": cached,
        "remaining_compressed_bytes": remaining,
        "cached_compressed_fraction": round(cached / total, 6) if total else 0.0,
        "all_layers_present_by_diff_id": remaining == 0,
        "layer_mapping_sha256": hashlib.sha256(
            json.dumps(paired, sort_keys=True).encode()
        ).hexdigest(),
    }


def inspect_image(
    image: str,
    *,
    local_diff_ids: set[str],
    proxy: str | None = None,
    timeout: int = 20,
) -> dict:
    repository, reference = _split_image(image)
    try:
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
        accounting = _account(manifest, config, local_diff_ids)
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"
        return {
            "image": image,
            "ready": False,
            "reason": "cache_accounting_error",
            "error_sha256": hashlib.sha256(detail.encode()).hexdigest(),
            "error_tail": detail[-500:],
        }
    return {
        "image": image,
        "ready": True,
        "reason": "cache_accounting_available",
        "manifest_sha256": manifest_meta.get("sha256"),
        "config_sha256": config_meta.get("sha256"),
        **accounting,
    }


def build(
    output: Path = OUT,
    *,
    proxy: str | None = None,
    timeout: int = 20,
) -> dict:
    frozen = json.loads(MANIFEST.read_text(encoding="utf-8"))
    try:
        local = _local_diff_ids(timeout=timeout)
        local_error = None
    except Exception as exc:
        local = set()
        local_error = hashlib.sha256(f"{type(exc).__name__}: {exc}".encode()).hexdigest()
    rows = []
    for task in frozen["tasks"]:
        row = inspect_image(
            task["image"],
            local_diff_ids=local,
            proxy=proxy,
            timeout=timeout,
        )
        row["instance_id"] = task["instance_id"]
        rows.append(row)
    result = {
        "schema": "e1c-strict-v5-cache-accounting-v1",
        "diagnostic_only": True,
        "changes_admission_gate": False,
        "ready_count": sum(row["ready"] for row in rows),
        "required_count": len(rows),
        "local_diff_id_count": len(local),
        "local_inventory_error_sha256": local_error,
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
    args = parser.parse_args()
    print(json.dumps(build(proxy=args.proxy, timeout=args.timeout), indent=2))
