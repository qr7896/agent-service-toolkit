"""Compare frozen DEV12 Docker Hub manifests with a direct-access mirror.

This is metadata-only: no blob endpoint, image pull, or model call is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from evals.e1c_evaluation_2 import IDENTITY, ROOT
from evals.e1c_evaluation_2_metadata import OUT as METADATA

OUT = ROOT / ".codex/e1c/evaluation_2/dev12_image_transport.json"
_IMAGE = re.compile(r"^swebench/(sweb\.eval\.x86_64\.[a-z0-9_.-]+):latest$")
_ACCEPT = ", ".join((
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
))


def _get(url: str, *, proxy: str | None, token: str | None = None) -> bytes:
    """Cap each HTTPS metadata response; an empty ProxyHandler bypasses OS proxy."""
    if not url.startswith("https://"):
        raise ValueError("metadata transport requires HTTPS")
    handler = urllib.request.ProxyHandler({"https": proxy} if proxy else {})
    opener = urllib.request.build_opener(handler)
    headers = {"Accept": _ACCEPT, "User-Agent": "curl/8.0.1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with opener.open(urllib.request.Request(url, headers=headers), timeout=15) as response:
        body = response.read(200_001)
    if len(body) > 200_000:
        raise ValueError("metadata response exceeds 200 KB")
    return body


def _token(repository: str, *, mirror: bool, proxy: str | None) -> str:
    if mirror:
        realm, service = "https://docker.1ms.run/openapi/v1/auth/token", "docker.1ms.run"
    else:
        realm, service = "https://auth.docker.io/token", "registry.docker.io"
    query = urllib.parse.urlencode({"service": service, "scope": f"repository:{repository}:pull"})
    value = json.loads(_get(f"{realm}?{query}", proxy=proxy)).get("token")
    if not isinstance(value, str) or not value:
        raise ValueError("registry token unavailable")
    return value


def _manifest(repository: str, *, mirror: bool, proxy: str | None, mirror_host: str = "docker.1ms.run") -> dict:
    host = mirror_host if mirror else "registry-1.docker.io"
    token = None if mirror and mirror_host == "docker.1panel.live" else _token(repository, mirror=mirror, proxy=proxy)
    base = f"https://{host}/v2/{repository}/manifests/"
    top = _get(base + "latest", proxy=proxy, token=token)
    top_digest = "sha256:" + hashlib.sha256(top).hexdigest()
    payload = json.loads(top)
    if "manifests" in payload:
        matches = [
            item for item in payload["manifests"]
            if item.get("platform", {}).get("os") == "linux"
            and item.get("platform", {}).get("architecture") == "amd64"
        ]
        if len(matches) != 1:
            raise ValueError("linux/amd64 manifest is ambiguous")
        platform_digest = matches[0]["digest"]
        raw = _get(base + platform_digest, proxy=proxy, token=token)
        if "sha256:" + hashlib.sha256(raw).hexdigest() != platform_digest:
            raise ValueError("platform manifest digest mismatch")
        payload = json.loads(raw)
    else:
        platform_digest = top_digest
    layers = payload.get("layers", [])
    if not layers or any(not isinstance(item.get("size"), int) or item["size"] < 0 for item in layers):
        raise ValueError("manifest has no valid layer sizes")
    return {
        "top_digest": top_digest,
        "platform_digest": platform_digest,
        "compressed_layer_bytes": sum(item["size"] for item in layers),
        "layer_count": len(layers),
    }


def audit(
    metadata_path: Path = METADATA,
    output: Path = OUT,
    *,
    official_metadata_proxy: str | None,
    mirror_host: str = "docker.1ms.run",
) -> dict:
    if mirror_host not in {"docker.1ms.run", "docker.1panel.live"}:
        raise ValueError("unapproved mirror host")
    metadata_bytes = metadata_path.read_bytes()
    metadata = json.loads(metadata_bytes)
    if (
        metadata.get("schema") != "e1c-evaluation-2-dev12-official-metadata-v1"
        or metadata.get("identity_sha256") != hashlib.sha256(IDENTITY.read_bytes()).hexdigest()
        or len(metadata.get("tasks", [])) != 12
    ):
        raise ValueError("DEV12 metadata is not bound to frozen identity")
    rows = []
    for task in metadata["tasks"]:
        image = task["image"]
        match = _IMAGE.fullmatch(image)
        if not match:
            raise ValueError("unexpected official image reference")
        repository = "swebench/" + match.group(1)
        row = {"instance_id": task["instance_id"], "official_image": image}
        try:
            official = _manifest(repository, mirror=False, proxy=official_metadata_proxy, mirror_host=mirror_host)
            mirror = _manifest(repository, mirror=True, proxy=None, mirror_host=mirror_host)
            row.update({
                "official": official,
                "mirror": mirror,
                "digest_identical": official["top_digest"] == mirror["top_digest"]
                and official["platform_digest"] == mirror["platform_digest"],
            })
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            row.update({"digest_identical": False, "error_type": type(exc).__name__})
        rows.append(row)
    result = {
        "schema": "e1c-evaluation-2-dev12-image-transport-v1",
        "metadata_sha256": hashlib.sha256(metadata_bytes).hexdigest(),
        "identity_sha256": metadata["identity_sha256"],
        "mirror_host": mirror_host,
        "official_proxy_used_for_metadata_only": bool(official_metadata_proxy),
        "mirror_os_proxy_bypassed": True,
        "max_response_bytes": 200_000,
        "blob_requests": 0,
        "image_pulls": 0,
        "provider_calls": 0,
        "digest_identical_count": sum(row["digest_identical"] for row in rows),
        "rows": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-metadata-proxy", default=None)
    parser.add_argument("--mirror-host", choices=("docker.1ms.run", "docker.1panel.live"), default="docker.1ms.run")
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    result = audit(output=args.output, official_metadata_proxy=args.official_metadata_proxy, mirror_host=args.mirror_host)
    print(json.dumps({"digest_identical_count": result["digest_identical_count"], "total": len(result["rows"])}))
