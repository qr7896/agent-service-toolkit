"""Bounded Docker Hub layer-throughput preflight for frozen strict-v5 images."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import time
import urllib.parse
from pathlib import Path

from evals.e1c_admission import ROOT

MANIFEST = ROOT / "data" / "e1c_strict_v5_canary_manifest.json"
OUT = ROOT / "data" / "e1c_strict_v5_blob_preflight.json"
LEDGER = ROOT / "data" / "e1c_strict_v5_blob_preflight_ledger.jsonl"
REGISTRY = "https://registry-1.docker.io"
AUTH = "https://auth.docker.io/token"
INDEX_ACCEPT = ", ".join(
    (
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    )
)
MANIFEST_ACCEPT = ", ".join(
    (
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    )
)


class CurlTransferError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        partial_bytes_received: int | None = None,
        requested_bytes: int | None = None,
    ) -> None:
        super().__init__(message)
        self.partial_bytes_received = partial_bytes_received
        self.requested_bytes = requested_bytes


def _partial_transfer_counts(detail: str) -> tuple[int | None, int | None]:
    match = re.search(r"with (\d+) out of (\d+) bytes received", detail)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def _split_image(image: str) -> tuple[str, str]:
    repository, sep, reference = image.rpartition(":")
    if not sep or "/" not in repository:
        raise ValueError(f"unsupported Docker Hub image reference: {image}")
    return repository, reference


def _curl(
    proxy: str | None,
    url: str,
    headers: dict[str, str],
    timeout: int,
    *,
    byte_range: str | None = None,
) -> bytes:
    curl = shutil.which("curl.exe") or shutil.which("curl")
    if not curl:
        raise RuntimeError("curl_unavailable")
    command = [
        curl,
        "-sS",
        "-L",
        "--connect-timeout",
        str(min(timeout, 5)),
        "--max-time",
        str(timeout),
    ]
    if proxy:
        command.extend(["--proxy", proxy])
    if byte_range:
        command.extend(["--range", byte_range])
    for key, value in headers.items():
        command.extend(["-H", f"{key}: {value}"])
    command.append(url)
    completed = subprocess.run(
        command,
        capture_output=True,
        timeout=timeout + 5,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode(errors="replace").strip()
        partial_bytes, requested_bytes = _partial_transfer_counts(detail)
        raise CurlTransferError(
            f"curl_exit_{completed.returncode}: {detail[-300:]}",
            partial_bytes_received=partial_bytes,
            requested_bytes=requested_bytes,
        )
    return completed.stdout


def _json_get(
    proxy: str | None,
    url: str,
    headers: dict[str, str],
    timeout: int,
) -> tuple[dict, dict]:
    raw = _curl(proxy, url, headers, timeout)
    payload = json.loads(raw)
    return payload, {
        "status": 200,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def _token(proxy: str | None, repository: str, timeout: int) -> str:
    query = urllib.parse.urlencode(
        {
            "service": "registry.docker.io",
            "scope": f"repository:{repository}:pull",
        }
    )
    payload, _ = _json_get(proxy, f"{AUTH}?{query}", {}, timeout)
    token = payload.get("token") or payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise RuntimeError("dockerhub_token_missing")
    return token


def _platform_manifest(
    proxy: str | None,
    repository: str,
    reference: str,
    token: str,
    timeout: int,
) -> tuple[dict, dict]:
    base = f"{REGISTRY}/v2/{repository}/manifests/"
    auth = {"Authorization": f"Bearer {token}"}
    payload, metadata = _json_get(
        proxy,
        base + reference,
        {**auth, "Accept": INDEX_ACCEPT},
        timeout,
    )
    manifests = payload.get("manifests")
    if not manifests:
        return payload, metadata
    matches = [
        row
        for row in manifests
        if row.get("platform", {}).get("architecture") == "amd64"
        and row.get("platform", {}).get("os") == "linux"
    ]
    if len(matches) != 1:
        raise RuntimeError("linux_amd64_manifest_ambiguous")
    digest = matches[0].get("digest")
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        raise RuntimeError("linux_amd64_manifest_digest_invalid")
    return _json_get(
        proxy,
        base + digest,
        {**auth, "Accept": MANIFEST_ACCEPT},
        timeout,
    )


def _select_layer(payload: dict) -> dict:
    layers = [
        row
        for row in payload.get("layers", [])
        if isinstance(row.get("digest"), str)
        and row["digest"].startswith("sha256:")
        and isinstance(row.get("size"), int)
        and row["size"] > 0
    ]
    if not layers:
        raise RuntimeError("manifest_has_no_layers")
    return max(layers, key=lambda row: row["size"])


def _total_layer_bytes(payload: dict) -> int:
    sizes = [
        row.get("size")
        for row in payload.get("layers", [])
        if isinstance(row.get("size"), int) and row["size"] > 0
    ]
    if not sizes:
        raise RuntimeError("manifest_has_no_layer_sizes")
    return sum(sizes)


def _probe_blob(
    proxy: str | None,
    repository: str,
    digest: str,
    token: str,
    *,
    sample_bytes: int,
    timeout: int,
) -> dict:
    started = time.monotonic()
    data = _curl(
        proxy,
        f"{REGISTRY}/v2/{repository}/blobs/{digest}",
        {
            "Authorization": f"Bearer {token}",
            "Accept-Encoding": "identity",
        },
        timeout,
        byte_range=f"0-{sample_bytes - 1}",
    )[:sample_bytes]
    duration = max(time.monotonic() - started, 1e-6)
    return {
        "status": 200,
        "bytes_read": len(data),
        "sample_bytes": sample_bytes,
        "duration_seconds": round(duration, 3),
        "bytes_per_second": round(len(data) / duration, 1),
        "range_requested": True,
        "sample_sha256": hashlib.sha256(data).hexdigest(),
    }


def probe_image(
    image: str,
    *,
    proxy: str | None = None,
    sample_bytes: int = 1024 * 1024,
    timeout: int = 30,
    min_bytes: int = 512 * 1024,
    min_bytes_per_second: int = 64 * 1024,
    max_estimated_seconds: int | None = None,
) -> dict:
    repository, reference = _split_image(image)
    try:
        token = _token(proxy, repository, timeout)
        platform_manifest, manifest_metadata = _platform_manifest(
            proxy, repository, reference, token, timeout
        )
        layer = _select_layer(platform_manifest)
        total_layer_bytes = _total_layer_bytes(platform_manifest)
        blob = _probe_blob(
            proxy,
            repository,
            layer["digest"],
            token,
            sample_bytes=sample_bytes,
            timeout=timeout,
        )
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"
        result = {
            "image": image,
            "ready": False,
            "reason": "blob_preflight_error",
            "error_sha256": hashlib.sha256(detail.encode()).hexdigest(),
            "error_tail": detail[-500:],
        }
        if isinstance(exc, CurlTransferError):
            result["partial_bytes_received"] = exc.partial_bytes_received
            result["requested_bytes"] = exc.requested_bytes
        return result
    estimated_seconds = total_layer_bytes / max(blob["bytes_per_second"], 1)
    budget_ready = (
        max_estimated_seconds is None
        or estimated_seconds <= max_estimated_seconds
    )
    ready = (
        blob["bytes_read"] >= min_bytes
        and blob["bytes_per_second"] >= min_bytes_per_second
        and budget_ready
    )
    return {
        "image": image,
        "ready": ready,
        "reason": (
            "blob_transport_ready"
            if ready
            else "blob_transport_exceeds_pull_budget"
            if not budget_ready
            else "blob_transport_too_slow"
        ),
        "manifest": manifest_metadata,
        "selected_layer": {
            "digest": layer["digest"],
            "size": layer["size"],
        },
        "total_layer_bytes": total_layer_bytes,
        "estimated_full_image_seconds": round(estimated_seconds, 1),
        "blob_probe": blob,
        "thresholds": {
            "min_bytes": min_bytes,
            "min_bytes_per_second": min_bytes_per_second,
            "max_estimated_seconds": max_estimated_seconds,
        },
    }


def run(
    *,
    proxy: str | None = None,
    sample_bytes: int = 1024 * 1024,
    timeout: int = 30,
    min_bytes: int = 512 * 1024,
    min_bytes_per_second: int = 64 * 1024,
    max_estimated_seconds: int | None = None,
    output: Path = OUT,
    ledger: Path | None = LEDGER,
) -> dict:
    frozen = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = []
    for task in frozen["tasks"]:
        row = probe_image(
            task["image"],
            proxy=proxy,
            sample_bytes=sample_bytes,
            timeout=timeout,
            min_bytes=min_bytes,
            min_bytes_per_second=min_bytes_per_second,
            max_estimated_seconds=max_estimated_seconds,
        )
        row["instance_id"] = task["instance_id"]
        rows.append(row)
        if not row["ready"]:
            break
    ready = len(rows) == len(frozen["tasks"]) and all(row["ready"] for row in rows)
    result = {
        "schema": "e1c-strict-v5-blob-preflight-v1",
        "ready": ready,
        "reason": "all_frozen_blob_transports_ready" if ready else "blob_transport_gate_incomplete",
        "checked_count": len(rows),
        "required_count": len(frozen["tasks"]),
        "network_exit": {
            "explicit_proxy": bool(proxy),
            "proxy_value_recorded": False,
        },
        "provider_calls": 0,
        "live_model_run": False,
        "rows": rows,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if ledger is not None:
        evidence = {
            "schema": "e1c-strict-v5-blob-preflight-evidence-v1",
            "result_sha256": hashlib.sha256(
                json.dumps(result, sort_keys=True).encode()
            ).hexdigest(),
            "ready": result["ready"],
            "reason": result["reason"],
            "checked_count": result["checked_count"],
            "required_count": result["required_count"],
            "network_exit": result["network_exit"],
            "rows": [
                {
                    "instance_id": row["instance_id"],
                    "ready": row["ready"],
                    "reason": row["reason"],
                    "bytes_per_second": row.get("blob_probe", {}).get(
                        "bytes_per_second"
                    ),
                    "total_layer_bytes": row.get("total_layer_bytes"),
                    "estimated_full_image_seconds": row.get(
                        "estimated_full_image_seconds"
                    ),
                    "error_sha256": row.get("error_sha256"),
                    "partial_bytes_received": row.get("partial_bytes_received"),
                    "requested_bytes": row.get("requested_bytes"),
                }
                for row in rows
            ],
            "provider_calls": 0,
            "live_model_run": False,
        }
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(evidence, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--proxy")
    parser.add_argument("--sample-bytes", type=int, default=1024 * 1024)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--min-bytes", type=int, default=512 * 1024)
    parser.add_argument("--min-bytes-per-second", type=int, default=64 * 1024)
    parser.add_argument("--max-estimated-seconds", type=int)
    args = parser.parse_args()
    print(
        json.dumps(
            run(
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
