"""Authoritative digest evidence for frozen strict-v5 image identity."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_blob_preflight import (
    _platform_manifest,
    _token,
)
from evals.e1c_strict_v5_blob_preflight import (
    _split_image as _split_registry_image,
)

MANIFEST = ROOT / "data" / "e1c_strict_v5_canary_manifest.json"
TRANSPORT = ROOT / "data" / "e1c_strict_v5_image_transport.json"
OUT = ROOT / "data" / "e1c_strict_v5_image_identity.json"


def _valid_digest(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    hex_part = value.removeprefix("sha256:")
    return len(hex_part) == 64 and all(ch in "0123456789abcdef" for ch in hex_part)


def _split_image(image: str) -> tuple[str, str]:
    name, sep, tag = image.rpartition(":")
    if not sep or "/" not in name:
        raise ValueError(f"unsupported image reference: {image}")
    return name, tag


def _dockerhub_tag_api(
    image: str,
    timeout: int = 8,
    proxy: str | None = None,
) -> dict:
    try:
        name, tag = _split_image(image)
    except ValueError as exc:
        return {"ready": False, "status": "invalid_image_reference", "error": str(exc)}
    curl = shutil.which("curl") or shutil.which("curl.exe")
    if not curl:
        return {"ready": False, "status": "curl_unavailable"}
    url = f"https://hub.docker.com/v2/repositories/{name}/tags/{tag}"
    try:
        command = [
            curl,
            "-sS",
            "--connect-timeout",
            str(min(timeout, 5)),
            "--max-time",
            str(timeout),
        ]
        if proxy:
            command.extend(["--proxy", proxy])
        command.append(url)
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout + 2,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ready": False, "status": "tag_api_timeout"}
    if completed.returncode != 0:
        detail = completed.stderr.strip()
        return {
            "ready": False,
            "status": "tag_api_transport_error",
            "exit_code": completed.returncode,
            "error_sha256": hashlib.sha256(detail.encode()).hexdigest(),
            "error_tail": detail[-500:],
        }
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"ready": False, "status": "tag_api_invalid_json"}
    platform_rows = [
        row
        for row in payload.get("images", [])
        if row.get("architecture") == "amd64" and row.get("os") == "linux"
    ]
    platform_digest = (
        platform_rows[0].get("digest") if len(platform_rows) == 1 else None
    )
    top_digest = payload.get("digest")
    ready = _valid_digest(platform_digest)
    return {
        "ready": ready,
        "status": "tag_api_digest_available" if ready else "tag_api_platform_ambiguous",
        "digest": platform_digest if ready else None,
        "tag_digest": top_digest if _valid_digest(top_digest) else None,
        "platform": {"architecture": "amd64", "os": "linux"} if ready else None,
        "platform_count": len(platform_rows),
    }


def _dockerhub_registry_digest(
    image: str,
    timeout: int = 12,
    proxy: str | None = None,
) -> dict:
    try:
        repository, reference = _split_registry_image(image)
        token = _token(proxy, repository, timeout)
        _, metadata = _platform_manifest(
            proxy,
            repository,
            reference,
            token,
            timeout,
        )
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"
        return {
            "ready": False,
            "status": "registry_v2_transport_error",
            "error_sha256": hashlib.sha256(detail.encode()).hexdigest(),
            "error_tail": detail[-500:],
        }
    body_sha = metadata.get("sha256")
    digest = f"sha256:{body_sha}" if isinstance(body_sha, str) else None
    ready = _valid_digest(digest)
    return {
        "ready": ready,
        "status": (
            "registry_v2_platform_digest_available"
            if ready
            else "registry_v2_platform_digest_invalid"
        ),
        "digest": digest if ready else None,
        "platform": {"architecture": "amd64", "os": "linux"} if ready else None,
        "manifest_bytes": metadata.get("bytes"),
    }


def _transport_rows() -> dict[str, dict]:
    if not TRANSPORT.exists():
        return {}
    payload = json.loads(TRANSPORT.read_text(encoding="utf-8"))
    return {row["instance_id"]: row for row in payload.get("rows", [])}


def _consensus(*digests: str | None) -> tuple[str | None, str]:
    valid = [value for value in digests if _valid_digest(value)]
    if not valid:
        return None, "authoritative_digest_unavailable"
    if len(set(valid)) != 1:
        return None, "authoritative_digest_conflict"
    return valid[0], "authoritative_digest_consensus"


def build(
    output: Path = OUT,
    tag_timeout: int = 8,
    registry_timeout: int = 12,
    proxy: str | None = None,
) -> dict:
    frozen = json.loads(MANIFEST.read_text(encoding="utf-8"))
    transport = _transport_rows()
    rows = []
    for task in frozen["tasks"]:
        instance_id = task["instance_id"]
        snapshot = transport.get(instance_id, {})
        official_snapshot = snapshot.get("official", {})
        mirror_snapshot = snapshot.get("mirror", {})
        registry_digest = (
            official_snapshot.get("digest")
            if official_snapshot.get("reachable") is True
            else None
        )
        registry_v2 = _dockerhub_registry_digest(
            task["image"],
            timeout=registry_timeout,
            proxy=proxy,
        )
        tag_api = _dockerhub_tag_api(
            task["image"],
            timeout=tag_timeout,
            proxy=proxy,
        )
        digest, status = _consensus(
            registry_digest,
            registry_v2.get("digest"),
            tag_api.get("digest"),
        )
        mirror_digest = (
            mirror_snapshot.get("digest")
            if mirror_snapshot.get("reachable") is True
            else None
        )
        mirror_equivalent = bool(
            digest
            and mirror_digest == digest
            and mirror_snapshot.get("platform", {}).get("architecture") == "amd64"
            and mirror_snapshot.get("platform", {}).get("os") == "linux"
        )
        rows.append(
            {
                "instance_id": instance_id,
                "official_image": task["image"],
                "registry_manifest_digest": registry_digest,
                "dockerhub_registry_v2": registry_v2,
                "dockerhub_tag_api": tag_api,
                "authoritative_digest": digest,
                "identity_status": status,
                "mirror_image": snapshot.get("mirror_image"),
                "mirror_digest": mirror_digest,
                "mirror_digest_equivalent": mirror_equivalent,
                "mirror_transport_admissible": mirror_equivalent,
            }
        )
    authoritative_ready = sum(bool(row["authoritative_digest"]) for row in rows)
    equivalent_ready = sum(row["mirror_digest_equivalent"] for row in rows)
    mismatch_count = sum(
        bool(row["authoritative_digest"])
        and bool(row["mirror_digest"])
        and not row["mirror_digest_equivalent"]
        for row in rows
    )
    result = {
        "schema": "e1c-strict-v5-image-identity-v1",
        "authoritative_ready_count": authoritative_ready,
        "mirror_equivalent_count": equivalent_ready,
        "mirror_mismatch_count": mismatch_count,
        "mirror_route_conclusively_closed": mismatch_count > 0,
        "ready": authoritative_ready == len(rows),
        "mirror_transport_ready": equivalent_ready == len(rows),
        "network_exit": {
            "explicit_proxy": bool(proxy),
            "proxy_value_recorded": False,
        },
        "provider_calls": 0,
        "live_model_run": False,
        "rows": rows,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--tag-timeout", type=int, default=8)
    parser.add_argument("--registry-timeout", type=int, default=12)
    parser.add_argument("--proxy")
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                tag_timeout=args.tag_timeout,
                registry_timeout=args.registry_timeout,
                proxy=args.proxy,
            ),
            indent=2,
        )
    )
