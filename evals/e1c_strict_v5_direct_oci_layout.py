"""Build an exact OCI layout from Docker Hub manifests and verified blobs."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path

from evals.e1c_strict_v5_blob_preflight import (
    INDEX_ACCEPT,
    MANIFEST_ACCEPT,
    REGISTRY,
    _curl,
    _split_image,
    _token,
)

OCI_LAYOUT = {"imageLayoutVersion": "1.0.0"}
REF_ANNOTATION = "org.opencontainers.image.ref.name"


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _blob_path(root: Path, digest: str) -> Path:
    algorithm, value = digest.split(":", 1)
    return root / "blobs" / algorithm / value


def _remaining(started: float, total_timeout: int) -> int:
    seconds = total_timeout - (time.monotonic() - started)
    if seconds <= 1:
        raise TimeoutError("direct_oci_total_timeout")
    return max(1, int(seconds))


def _manifest_raw(
    proxy: str | None,
    repository: str,
    reference: str,
    token: str,
    timeout: int,
    accept: str,
) -> bytes:
    return _curl(
        proxy,
        f"{REGISTRY}/v2/{repository}/manifests/{reference}",
        {"Authorization": f"Bearer {token}", "Accept": accept},
        timeout,
    )


def _linux_amd64_descriptor(payload: dict) -> dict | None:
    manifests = payload.get("manifests")
    if not manifests:
        return None
    matches = [
        row
        for row in manifests
        if row.get("platform", {}).get("os") == "linux"
        and row.get("platform", {}).get("architecture") == "amd64"
    ]
    if len(matches) != 1:
        raise RuntimeError("linux_amd64_manifest_ambiguous")
    return matches[0]


def _write_verified_bytes(root: Path, digest: str, data: bytes) -> None:
    if _sha256_bytes(data) != digest:
        raise RuntimeError("descriptor_digest_mismatch")
    path = _blob_path(root, digest)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _download_verified_blob(
    *,
    proxy: str | None,
    repository: str,
    digest: str,
    expected_size: int,
    token: str,
    destination: Path,
    timeout: int,
) -> dict:
    curl = shutil.which("curl.exe") or shutil.which("curl")
    if not curl:
        raise RuntimeError("curl_unavailable")
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        curl,
        "-sS",
        "-L",
        "--fail",
        "--connect-timeout",
        str(min(timeout, 5)),
        "--max-time",
        str(timeout),
    ]
    if proxy:
        command.extend(["--proxy", proxy])
    command.extend(
        [
            "-H",
            f"Authorization: Bearer {token}",
            "-H",
            "Accept-Encoding: identity",
            "--output",
            str(destination),
            f"{REGISTRY}/v2/{repository}/blobs/{digest}",
        ]
    )
    started = time.monotonic()
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout + 5,
        check=False,
    )
    duration = max(time.monotonic() - started, 1e-6)
    if completed.returncode != 0:
        raise RuntimeError(
            f"blob_download_failed_{completed.returncode}: {completed.stderr[-300:]}"
        )
    size = destination.stat().st_size
    hasher = hashlib.sha256()
    with destination.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    actual_digest = "sha256:" + hasher.hexdigest()
    if actual_digest != digest:
        raise RuntimeError("blob_digest_mismatch")
    if size != expected_size:
        raise RuntimeError("blob_size_mismatch")
    return {
        "digest": digest,
        "bytes": size,
        "duration_seconds": round(duration, 3),
        "bytes_per_second": round(size / duration, 1),
    }


def build_archive(
    image: str,
    *,
    proxy: str | None,
    timeout: int,
    output_tar: Path,
) -> dict:
    started = time.monotonic()
    repository, reference = _split_image(image)
    token = _token(proxy, repository, _remaining(started, timeout))
    top_raw = _manifest_raw(
        proxy,
        repository,
        reference,
        token,
        _remaining(started, timeout),
        INDEX_ACCEPT,
    )
    top_digest = _sha256_bytes(top_raw)
    top_payload = json.loads(top_raw)
    selected = _linux_amd64_descriptor(top_payload)
    if selected is None:
        platform_raw = top_raw
        platform_digest = top_digest
        platform_payload = top_payload
    else:
        platform_digest = selected.get("digest")
        if not isinstance(platform_digest, str) or not platform_digest.startswith(
            "sha256:"
        ):
            raise RuntimeError("linux_amd64_manifest_digest_invalid")
        platform_raw = _manifest_raw(
            proxy,
            repository,
            platform_digest,
            token,
            _remaining(started, timeout),
            MANIFEST_ACCEPT,
        )
        if _sha256_bytes(platform_raw) != platform_digest:
            raise RuntimeError("platform_manifest_digest_mismatch")
        platform_payload = json.loads(platform_raw)

    work = Path(tempfile.mkdtemp(prefix="e1c-oci-layout-"))
    rows = []
    try:
        (work / "oci-layout").write_text(
            json.dumps(OCI_LAYOUT) + "\n",
            encoding="utf-8",
        )
        _write_verified_bytes(work, top_digest, top_raw)
        if platform_digest != top_digest:
            _write_verified_bytes(work, platform_digest, platform_raw)
        descriptors = [
            platform_payload.get("config", {}),
            *platform_payload.get("layers", []),
        ]
        for descriptor in descriptors:
            digest = descriptor.get("digest")
            size = descriptor.get("size")
            if not isinstance(digest, str) or not digest.startswith("sha256:"):
                raise RuntimeError("blob_descriptor_digest_invalid")
            if not isinstance(size, int) or size < 0:
                raise RuntimeError("blob_descriptor_size_invalid")
            rows.append(
                _download_verified_blob(
                    proxy=proxy,
                    repository=repository,
                    digest=digest,
                    expected_size=size,
                    token=token,
                    destination=_blob_path(work, digest),
                    timeout=_remaining(started, timeout),
                )
            )
        media_type = top_payload.get("mediaType")
        if not isinstance(media_type, str) or not media_type:
            media_type = (
                "application/vnd.oci.image.index.v1+json"
                if selected is not None
                else "application/vnd.oci.image.manifest.v1+json"
            )
        local_index = {
            "schemaVersion": 2,
            "manifests": [
                {
                    "mediaType": media_type,
                    "digest": top_digest,
                    "size": len(top_raw),
                    "annotations": {REF_ANNOTATION: image},
                }
            ],
        }
        (work / "index.json").write_text(
            json.dumps(local_index, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        output_tar.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(output_tar, "w") as archive:
            for path in sorted(work.rglob("*")):
                archive.add(path, arcname=path.relative_to(work))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return {
        "schema": "e1c-strict-v5-direct-oci-layout-v1",
        "image": image,
        "top_level_digest": top_digest,
        "platform_digest": platform_digest,
        "config_digest": platform_payload.get("config", {}).get("digest"),
        "blob_count": len(rows),
        "downloaded_bytes": sum(row["bytes"] for row in rows),
        "duration_seconds": round(time.monotonic() - started, 3),
        "archive_sha256": hashlib.sha256(output_tar.read_bytes()).hexdigest(),
        "network_exit": {
            "explicit_proxy": bool(proxy),
            "proxy_value_recorded": False,
        },
        "provider_calls": 0,
        "live_model_run": False,
        "rows": rows,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--proxy")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--output-tar", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    args = parser.parse_args()
    result = build_archive(
        args.image,
        proxy=args.proxy,
        timeout=args.timeout,
        output_tar=args.output_tar,
    )
    args.metadata.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
