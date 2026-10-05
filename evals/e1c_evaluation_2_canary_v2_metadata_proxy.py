"""Frozen infrastructure amendment: official metadata via 7892, image bytes direct."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import urllib.parse
import urllib.request

from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_canary_v2_select import FREEZE as ORIGINAL_FREEZE
from evals.e1c_evaluation_2_canary_v2_select import IDENTITY
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_image_transport import _ACCEPT

RUN_ID = "e1c2-canary-v2-metadata-proxy-v1"
ORIGINAL_OUT = ROOT / ".codex/e1c/evaluation_2/canary-v2"
METADATA = ORIGINAL_OUT / "metadata.json"
OUT = ROOT / ".codex/e1c/evaluation_2/canary-v2-metadata-proxy-v1"
TRANSPORT = OUT / "image_transport.json"
FREEZE = ROOT / "data/e1c_evaluation_2_canary_v2_transport_amendment.json"
PROTOCOL = ROOT / "docs/research/E1C2_CANARY_V2_METADATA_PROXY_AMENDMENT_2026-10-05.md"
PROXY = "http://127.0.0.1:7892"
RESPONSE_CAP = 200_000
OFFICIAL_BYTE_CAP = 2_000_000
OFFICIAL_REQUEST_CAP = 9
IMAGE = re.compile(r"swebench/(sweb\.eval\.x86_64\.[a-z0-9_.-]+):latest\Z")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("metadata redirects are disabled")


class MetadataClient:
    """No blob URL can enter this bounded, non-redirecting metadata client."""

    def __init__(self) -> None:
        self.official_bytes = 0
        self.official_requests = 0
        self.mirror_bytes = 0
        self.mirror_requests = 0

    def get(self, url: str, *, token: str | None = None) -> bytes:
        parsed = urllib.parse.urlsplit(url)
        official = parsed.hostname in {"auth.docker.io", "registry-1.docker.io"}
        token_url = parsed.hostname == "auth.docker.io" and parsed.path == "/token"
        manifest_url = parsed.hostname in {"registry-1.docker.io", "docker.1panel.live"} and re.fullmatch(
            r"/v2/swebench/sweb\.eval\.x86_64\.[a-z0-9_.-]+/manifests/(?:latest|sha256:[0-9a-f]{64})",
            parsed.path,
        )
        if (parsed.scheme != "https" or parsed.port not in (None, 443) or parsed.username
                or parsed.password or parsed.fragment or not (token_url or manifest_url)
                or (manifest_url and parsed.query) or (token and parsed.hostname != "registry-1.docker.io")):
            raise ValueError("only approved official token and manifest metadata URLs are allowed")
        if official and (self.official_requests >= OFFICIAL_REQUEST_CAP or self.official_bytes >= OFFICIAL_BYTE_CAP):
            raise ValueError("official metadata budget exceeded")
        if not official and self.mirror_requests >= 6:
            raise ValueError("mirror metadata request budget exceeded")
        limit = min(RESPONSE_CAP, OFFICIAL_BYTE_CAP - self.official_bytes) if official else RESPONSE_CAP
        headers = {"Accept": _ACCEPT, "Accept-Encoding": "identity", "User-Agent": "e1c2-metadata-amendment"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({"https": PROXY} if official else {}), _NoRedirect(),
        )
        if official:
            self.official_requests += 1
        else:
            self.mirror_requests += 1
        with opener.open(urllib.request.Request(url, headers=headers), timeout=20) as response:
            content_length = response.headers.get("Content-Length")
            if content_length is not None and int(content_length) > limit:
                raise ValueError("metadata response exceeds remaining byte budget")
            raw = response.read(limit + 1)
        if official:
            self.official_bytes += len(raw)
        else:
            self.mirror_bytes += len(raw)
        if len(raw) > limit:
            raise ValueError("metadata response exceeds remaining byte budget")
        return raw

    def manifest(self, repository: str, *, official: bool) -> dict:
        token = None
        if official:
            query = urllib.parse.urlencode({"service": "registry.docker.io", "scope": f"repository:{repository}:pull"})
            token = json.loads(self.get("https://auth.docker.io/token?" + query)).get("token")
            if not isinstance(token, str) or not token:
                raise ValueError("official registry token unavailable")
        host = "registry-1.docker.io" if official else "docker.1panel.live"
        url = f"https://{host}/v2/{repository}/manifests/"
        raw = self.get(url + "latest", token=token)
        top_digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        payload = json.loads(raw)
        platform_digest = top_digest
        if "manifests" in payload:
            matches = [item for item in payload["manifests"] if item.get("platform", {}).get("os") == "linux"
                       and item.get("platform", {}).get("architecture") == "amd64"]
            if len(matches) != 1 or not DIGEST.fullmatch(matches[0]["digest"]):
                raise ValueError("linux/amd64 manifest is ambiguous or invalid")
            platform_digest = matches[0]["digest"]
            raw = self.get(url + platform_digest, token=token)
            if "sha256:" + hashlib.sha256(raw).hexdigest() != platform_digest:
                raise ValueError("platform manifest digest mismatch")
            payload = json.loads(raw)
        layers = payload.get("layers", [])
        if not layers or any(type(item.get("size")) is not int or item["size"] < 0 for item in layers):
            raise ValueError("manifest has no valid layer sizes")
        return {"top_digest": top_digest, "platform_digest": platform_digest,
                "compressed_layer_bytes": sum(item["size"] for item in layers), "layer_count": len(layers)}


def amendment() -> dict:
    original = json.loads(ORIGINAL_FREEZE.read_bytes())
    if any(_sha(ROOT / name) != digest for name, digest in original["method_files"].items()):
        raise ValueError("original canary v2 method bytes changed")
    identity = json.loads(IDENTITY.read_bytes())
    metadata = json.loads(METADATA.read_bytes())
    if (identity.get("method_freeze_sha256") != _sha(ORIGINAL_FREEZE)
            or metadata.get("identity_sha256") != _sha(IDENTITY)
            or len(identity.get("tasks", [])) != 3
            or [row["instance_id"] for row in identity["tasks"]] != [row["instance_id"] for row in metadata["tasks"]]):
        raise ValueError("original fixed cohort or official metadata changed")
    if any((ORIGINAL_OUT / name).exists() for name in ("live", "issue-only", "source", "grader-only", "acquire")):
        raise ValueError("original direct-only execution already started; amendment requires review")
    return {
        "schema": "e1c2-canary-v2-transport-amendment-v1", "run_id": RUN_ID,
        "role": "infrastructure_amendment_same_selected_cohort_not_a_new_sample",
        "original_method_freeze_sha256": _sha(ORIGINAL_FREEZE), "original_identity_sha256": _sha(IDENTITY),
        "official_metadata_sha256": _sha(METADATA), "fixed_denominator": 3,
        "amended_files": {str(path.relative_to(ROOT).as_posix()): _sha(path) for path in (
            ROOT / "evals/e1c_evaluation_2_canary_v2_metadata_proxy.py", PROTOCOL,
            ROOT / "evals/e1c_evaluation_2_mirror_acquire.py", ROOT / "evals/e1c_evaluation_2_image_transport.py",
            ROOT / "evals/e1c_evaluation_2_batch_acquire.py",
        )},
        "official_proxy_metadata_only": PROXY, "official_response_byte_cap": RESPONSE_CAP,
        "official_total_body_byte_cap": OFFICIAL_BYTE_CAP, "official_request_cap": OFFICIAL_REQUEST_CAP,
        "mirror_proxy": None, "redirects": 0, "metadata_retries": 0,
        "task_content_inspected": False, "outcome_inspected": False, "provider_calls": 0,
        "future_live_requires_amendment_bound_execution_identity": True,
    }


def freeze() -> dict:
    value = amendment()
    if FREEZE.exists():
        if json.loads(FREEZE.read_bytes()) != value:
            raise ValueError("transport amendment freeze changed")
    else:
        if OUT.exists():
            raise ValueError("amended execution started before its freeze")
        _save(FREEZE, value)
    return value


def require_freeze() -> None:
    if not FREEZE.is_file() or json.loads(FREEZE.read_bytes()) != amendment():
        raise ValueError("run freeze first; transport amendment missing or changed")


def checked_transport() -> dict:
    require_freeze()
    if not TRANSPORT.is_file():
        raise ValueError("run transport first; official/mirror digest seal missing")
    value = json.loads(TRANSPORT.read_bytes())
    tasks = json.loads(METADATA.read_bytes())["tasks"]
    if (value.get("amendment_sha256") != _sha(FREEZE) or value.get("identity_sha256") != _sha(IDENTITY)
            or value.get("metadata_sha256") != _sha(METADATA) or value.get("mirror_host") != "docker.1panel.live"
            or value.get("official_proxy_metadata_only") is not True or value.get("mirror_os_proxy_bypassed") is not True
            or len(value.get("rows", [])) != 3 or value.get("provider_calls") != 0
            or value.get("blob_requests") != 0 or value.get("image_pulls") != 0):
        raise ValueError("transport seal is not bound to the amendment")
    for task, row in zip(tasks, value["rows"], strict=True):
        if (row.get("instance_id") != task["instance_id"] or row.get("official_image") != task["image"]
                or row.get("digest_identical") is not True or row.get("official") != row.get("mirror")):
            raise ValueError("official/mirror digest or task order differs")
    return value


def audit() -> dict:
    require_freeze()
    if TRANSPORT.exists():
        return checked_transport()
    client = MetadataClient()
    result_rows = []
    for task in json.loads(METADATA.read_bytes())["tasks"]:
        if not IMAGE.fullmatch(task["image"]):
            raise ValueError("unexpected official image reference")
        repository = task["image"].removesuffix(":latest")
        official = client.manifest(repository, official=True)
        mirror = client.manifest(repository, official=False)
        if official != mirror:
            raise ValueError(f"official/mirror manifest differs: {task['instance_id']}")
        result_rows.append({"instance_id": task["instance_id"], "official_image": task["image"],
                            "repository": repository, "official": official, "mirror": mirror, "digest_identical": True})
        print(json.dumps({"verified": len(result_rows), "total": 3, "instance_id": task["instance_id"],
                          "compressed_gib": round(official["compressed_layer_bytes"] / 1024**3, 2),
                          "official_metadata_body_bytes": client.official_bytes}), flush=True)
    value = {"schema": "e1c2-canary-image-transport-metadata-proxy-v1", "run_id": RUN_ID,
             "amendment_sha256": _sha(FREEZE), "identity_sha256": _sha(IDENTITY), "metadata_sha256": _sha(METADATA),
             "mirror_host": "docker.1panel.live", "official_proxy_metadata_only": True,
             "mirror_os_proxy_bypassed": True, "official_metadata_body_bytes": client.official_bytes,
             "official_metadata_requests": client.official_requests, "mirror_metadata_body_bytes": client.mirror_bytes,
             "official_total_body_byte_cap": OFFICIAL_BYTE_CAP, "blob_requests": 0, "image_pulls": 0,
             "provider_calls": 0, "rows": result_rows}
    _save(TRANSPORT, value)
    return value


def bind_stage():
    checked_transport()
    from evals import e1c_evaluation_2_canary_v2_stage as stage

    stage.OUT, stage.TRANSPORT = OUT, TRANSPORT
    stage.ACQUIRE, stage.GRADER = OUT / "acquire", OUT / "grader-only"
    stage.PUBLIC, stage.SOURCE = OUT / "issue-only", OUT / "source"
    stage.bind()
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    return stage


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "transport", "download", "admit", "public"))
    parser.add_argument("--timeout-per-image", type=int, default=21600)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    if args.command == "freeze":
        result = freeze()
    elif args.command == "transport":
        result = audit()
    else:
        stage = bind_stage()
        if args.command == "download":
            docker = subprocess.run(["docker", "version", "--format", "{{.Server.Version}}"],
                                    capture_output=True, text=True, timeout=30, check=False)
            if docker.returncode or not docker.stdout.strip():
                raise RuntimeError("Docker engine unavailable; image acquisition has not started")
            result = stage.acquire.acquire(timeout_per_image=args.timeout_per_image)
        elif args.command == "admit":
            result = stage.admit(args.timeout)
        else:
            result = stage.public()
    print(json.dumps({"run_id": RUN_ID, "provider_calls": 0, "result": result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
