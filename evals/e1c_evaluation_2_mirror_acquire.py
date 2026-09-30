"""Acquire one frozen DEV12 image via verified OCI blobs and Docker archive.

Only the already-audited 1Panel mirror supplies bytes. Every manifest and blob
is checked against the frozen official digest chain before Docker import.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import http.client
import io
import json
import re
import shutil
import subprocess
import tarfile
import time
import urllib.request
from pathlib import Path

from evals.e1c_evaluation_2_image_transport import _get
from evals.e1c_evaluation_2_probe import verified_mirror_image
from evals.e1c_strict_v5_direct_oci_layout import _linux_amd64_descriptor

_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_HOST = "docker.1panel.live"
_BASE = f"https://{_HOST}/v2/"
_MAX_BLOB_CONNECTIONS = 32


def _digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _blob_path(root: Path, digest: str) -> Path:
    if not _DIGEST.fullmatch(digest):
        raise ValueError("invalid blob digest")
    return root / "blobs" / "sha256" / digest[7:]


def _manifest(repository: str, digest: str) -> bytes:
    if not _DIGEST.fullmatch(digest):
        raise ValueError("invalid manifest digest")
    raw = _get(f"{_BASE}{repository}/manifests/{digest}", proxy=None)
    if _digest(raw) != digest:
        raise ValueError("mirror manifest differs from frozen official digest")
    return raw


def _download_blob(repository: str, descriptor: dict, root: Path, deadline: float) -> dict:
    digest, size = descriptor.get("digest"), descriptor.get("size")
    if not isinstance(digest, str) or not _DIGEST.fullmatch(digest) or not isinstance(size, int) or size < 0:
        raise ValueError("invalid OCI blob descriptor")
    path = _blob_path(root, digest)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.stat().st_size == size and _file_digest(path) == digest:
        return {"digest": digest, "bytes": size, "reused": True}
    if path.exists():
        raise ValueError("existing complete blob differs from official descriptor")
    partial = path.with_name(path.name + ".partial")
    offset = partial.stat().st_size if partial.is_file() else 0
    if offset > size:
        raise ValueError("partial blob exceeds official descriptor size")
    hasher = hashlib.sha256()
    if offset:
        with partial.open("rb") as existing:
            for chunk in iter(lambda: existing.read(1024 * 1024), b""):
                hasher.update(chunk)
    if offset == size:
        if "sha256:" + hasher.hexdigest() != digest:
            raise ValueError("complete partial blob digest differs from official descriptor")
        partial.replace(path)
        return {"digest": digest, "bytes": size, "reused": True}
    headers = {"User-Agent": "curl/8.0.1", "Accept-Encoding": "identity"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    request = urllib.request.Request(
        f"{_BASE}{repository}/blobs/{digest}",
        headers=headers,
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    total = offset
    started = time.monotonic()
    last_report = started
    print(f"  resume {offset:,}/{size:,} bytes", flush=True)
    with opener.open(request, timeout=30) as response:
        expected_status = 206 if offset else 200
        expected_range = f"bytes {offset}-{size - 1}/{size}"
        if response.status != expected_status or response.headers.get("Content-Encoding") not in (None, "identity"):
            raise ValueError(f"mirror blob response is not raw HTTP {expected_status}")
        if offset and response.headers.get("Content-Range") != expected_range:
            raise ValueError("mirror blob resume range differs from official descriptor")
        content_length = response.headers.get("Content-Length")
        if content_length is not None and int(content_length) != size - offset:
            raise ValueError("mirror blob response length differs from official descriptor")
        with partial.open("ab" if offset else "wb") as output:
            while True:
                if time.monotonic() >= deadline:
                    raise TimeoutError("mirror blob acquisition deadline exceeded")
                # 256 KiB keeps progress visible even on a slow direct connection.
                chunk = response.read(min(256 * 1024, size - total + 1))
                if not chunk:
                    break
                total += len(chunk)
                if total > size:
                    raise ValueError("mirror blob exceeds official descriptor size")
                hasher.update(chunk)
                output.write(chunk)
                now = time.monotonic()
                if now - last_report >= 8 or total == size:
                    rate = (total - offset) / max(now - started, 0.001)
                    eta = (size - total) / rate if rate > 0 else float("inf")
                    print(
                        f"  {total / 1024**2:.1f}/{size / 1024**2:.1f} MiB "
                        f"({total / size:.1%}), {rate / 1024**2:.2f} MiB/s, ETA {eta / 60:.1f} min",
                        flush=True,
                    )
                    last_report = now
    if total != size or "sha256:" + hasher.hexdigest() != digest:
        raise ValueError(
            f"mirror blob differs from official descriptor: expected_bytes={size} received_bytes={total} "
            f"digest_match={'sha256:' + hasher.hexdigest() == digest}"
        )
    partial.replace(path)
    return {"digest": digest, "bytes": size, "reused": False, "resumed_from_bytes": offset}


def _file_digest(path: Path) -> str:
    with path.open("rb") as stream:
        return "sha256:" + hashlib.file_digest(stream, "sha256").hexdigest()


class _ProgressReader:
    """Expose archive copy progress without buffering a decompressed layer."""

    def __init__(self, stream: object, total: int, label: str) -> None:
        self.stream, self.total, self.label = stream, total, label
        self.done = 0
        self.last_report = time.monotonic()

    def read(self, size: int = -1) -> bytes:
        chunk = self.stream.read(size)
        self.done += len(chunk)
        now = time.monotonic()
        if now - self.last_report >= 15 or self.done == self.total:
            print(f"  {self.label}: {self.done / 1024**2:.1f}/{self.total / 1024**2:.1f} MiB", flush=True)
            self.last_report = now
        return chunk


def _download_blob_with_resume(repository: str, descriptor: dict, root: Path, deadline: float) -> dict:
    """Reconnect only after a partial blob grows; never retry a full bad digest."""
    partial = _blob_path(root, descriptor["digest"]).with_name(descriptor["digest"][7:] + ".partial")
    for attempt in range(1, _MAX_BLOB_CONNECTIONS + 1):
        before = partial.stat().st_size if partial.is_file() else 0
        try:
            return _download_blob(repository, descriptor, root, deadline)
        except (OSError, ValueError, http.client.IncompleteRead) as exc:
            after = partial.stat().st_size if partial.is_file() else 0
            if not (before < after < descriptor["size"] and attempt < _MAX_BLOB_CONNECTIONS and time.monotonic() < deadline):
                raise
            print(
                f"  incomplete transport at {after:,}/{descriptor['size']:,} bytes "
                f"({type(exc).__name__}); reconnect {attempt}/{_MAX_BLOB_CONNECTIONS - 1} using exact Range",
                flush=True,
            )
            time.sleep(1)
    raise RuntimeError("unreachable blob reconnect state")


def build_layout(
    instance_id: str, root: Path, *, timeout_seconds: int = 900, verified_reference: str | None = None,
) -> dict:
    """Download one exact digest chain; reusable verified blobs survive interruption."""
    if timeout_seconds < 1:
        raise ValueError("positive timeout required")
    reference = verified_reference or verified_mirror_image(instance_id, _HOST)
    if not re.fullmatch(r"docker\.1panel\.live/swebench/sweb\.eval\.x86_64\.[a-z0-9_.-]+@sha256:[0-9a-f]{64}", reference):
        raise ValueError("mirror reference must be an official-audited digest")
    repository, top_digest = reference.removeprefix(_HOST + "/").rsplit("@", 1)
    deadline = time.monotonic() + timeout_seconds
    top_raw = _manifest(repository, top_digest)
    top = json.loads(top_raw)
    selected = _linux_amd64_descriptor(top)
    platform_digest = selected["digest"] if selected else top_digest
    platform_raw = _manifest(repository, platform_digest) if selected else top_raw
    platform = json.loads(platform_raw)
    descriptors = [platform["config"], *platform["layers"]]
    if not platform["layers"]:
        raise ValueError("official platform manifest has no layers")
    expected_bytes = sum(item["size"] for item in descriptors)
    root.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(root.parent).free < expected_bytes * 2 + 2_000_000_000:
        raise RuntimeError("insufficient free space for verified OCI layout and archive")
    root.mkdir(parents=True, exist_ok=True)
    for digest, raw in ((top_digest, top_raw), (platform_digest, platform_raw)):
        path = _blob_path(root, digest)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_bytes() != raw:
            raise ValueError("existing OCI manifest blob differs")
        path.write_bytes(raw)
    rows = []
    for number, item in enumerate(descriptors, 1):
        print(f"blob {number}/{len(descriptors)} {item['digest'][7:19]} ({item['size']} bytes)", flush=True)
        rows.append(_download_blob_with_resume(repository, item, root, deadline))
    tag = f"e1c2/{instance_id.lower()}:verified"
    (root / "oci-layout").write_text('{"imageLayoutVersion":"1.0.0"}\n', encoding="utf-8")
    index = {
        "schemaVersion": 2,
        "manifests": [{
            "mediaType": top["mediaType"], "digest": top_digest,
            "size": len(top_raw),
            "annotations": {"org.opencontainers.image.ref.name": tag},
        }],
    }
    (root / "index.json").write_text(json.dumps(index, separators=(",", ":")) + "\n", encoding="utf-8")
    return {
        "schema": "e1c-evaluation-2-verified-mirror-acquisition-v1",
        "instance_id": instance_id,
        "mirror_reference": reference,
        "top_digest": top_digest,
        "platform_digest": platform_digest,
        "config_digest": platform["config"]["digest"],
        "local_tag": tag,
        "verified_blob_count": len(rows),
        "verified_blob_bytes": sum(row["bytes"] for row in rows),
        "proxy_bypassed": True,
        "provider_calls": 0,
        "rows": rows,
    }


def archive_layout(root: Path, output: Path) -> None:
    """Convert verified OCI blobs into the Docker archive format `docker load` expects."""
    if output.exists():
        print(f"reusing completed Docker archive: {output}", flush=True)
        return
    index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    descriptor = index["manifests"][0]
    top_path = _blob_path(root, descriptor["digest"])
    if _file_digest(top_path) != descriptor["digest"]:
        raise ValueError("OCI index manifest digest mismatch")
    top = json.loads(top_path.read_bytes())
    selected = _linux_amd64_descriptor(top)
    platform_digest = selected["digest"] if selected else descriptor["digest"]
    platform_path = _blob_path(root, platform_digest)
    if _file_digest(platform_path) != platform_digest:
        raise ValueError("OCI platform manifest digest mismatch")
    platform = json.loads(platform_path.read_bytes())
    config_digest = platform["config"]["digest"]
    config_path = _blob_path(root, config_digest)
    if _file_digest(config_path) != config_digest:
        raise ValueError("OCI config digest mismatch")
    config = json.loads(config_path.read_bytes())
    layers = platform["layers"]
    diff_ids = config["rootfs"]["diff_ids"]
    if not layers or len(layers) != len(diff_ids):
        raise ValueError("OCI layer and config diff-id counts differ")
    tag = descriptor["annotations"]["org.opencontainers.image.ref.name"]
    if not tag.startswith("e1c2/") or not tag.endswith(":verified"):
        raise ValueError("unexpected verified Docker image tag")
    layer_paths = []
    for number, (layer, diff_id) in enumerate(zip(layers, diff_ids, strict=True), 1):
        path = _blob_path(root, layer["digest"])
        if path.stat().st_size != layer["size"] or _file_digest(path) != layer["digest"]:
            raise ValueError("compressed OCI layer differs from official manifest")
        if not _DIGEST.fullmatch(diff_id):
            raise ValueError("invalid config diff-id")
        if layer["mediaType"] not in {
            "application/vnd.docker.image.rootfs.diff.tar.gzip",
            "application/vnd.oci.image.layer.v1.tar+gzip",
        }:
            raise ValueError("unsupported OCI layer compression")
        print(f"checking uncompressed layer {number}/{len(layers)}", flush=True)
        size = 0
        hasher = hashlib.sha256()
        last_report = time.monotonic()
        with gzip.open(path, "rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                size += len(chunk)
                hasher.update(chunk)
                if time.monotonic() - last_report >= 15:
                    print(f"  checked {size / 1024**2:.1f} MiB", flush=True)
                    last_report = time.monotonic()
        if "sha256:" + hasher.hexdigest() != diff_id:
            raise ValueError("uncompressed OCI layer differs from config diff-id")
        layer_paths.append((path, diff_id, size))
    uncompressed_bytes = sum(size for _, _, size in layer_paths)
    if shutil.disk_usage(root).free < uncompressed_bytes + 20 * 1024**3:
        raise RuntimeError("insufficient disk headroom to create Docker archive")
    partial = output.with_name(output.name + ".partial")
    print(f"creating Docker archive: {uncompressed_bytes / 1024**3:.2f} GiB uncompressed layers", flush=True)
    with tarfile.open(partial, "w") as archive:
        config_name = f"blobs/sha256/{config_digest[7:]}"
        _add_bytes(archive, config_name, config_path.read_bytes())
        names = []
        seen = set()
        for number, (path, diff_id, size) in enumerate(layer_paths, 1):
            name = f"blobs/sha256/{diff_id[7:]}"
            names.append(name)
            if name in seen:
                continue
            seen.add(name)
            print(f"archiving layer {number}/{len(layer_paths)} ({size / 1024**2:.1f} MiB)", flush=True)
            info = tarfile.TarInfo(name)
            info.size = size
            with gzip.open(path, "rb") as source:
                archive.addfile(info, _ProgressReader(source, size, f"archived layer {number}/{len(layer_paths)}"))
        manifest = [{"Config": config_name, "RepoTags": [tag], "Layers": names}]
        _add_bytes(archive, "manifest.json", json.dumps(manifest, separators=(",", ":")).encode())
        repository, version = tag.rsplit(":", 1)
        repositories = {repository: {version: diff_ids[-1][7:]}}
        _add_bytes(archive, "repositories", json.dumps(repositories, separators=(",", ":")).encode())
    partial.replace(output)


def _add_bytes(archive: tarfile.TarFile, name: str, value: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(value)
    archive.addfile(info, io.BytesIO(value))


def load_archive(archive: Path, expected_config_digest: str, tag: str) -> dict:
    print(f"loading verified Docker archive: {archive}", flush=True)
    started = time.monotonic()
    process = subprocess.Popen(
        ["docker", "load", "-i", str(archive)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    while True:
        try:
            stdout, stderr = process.communicate(timeout=15)
            break
        except subprocess.TimeoutExpired:
            print(f"  Docker import still running: {(time.monotonic() - started) / 60:.1f} min", flush=True)
    if process.returncode:
        raise RuntimeError(f"docker load failed: {stderr[-500:]}")
    inspect = subprocess.run(
        ["docker", "image", "inspect", tag, "--format", "{{.Id}}"],
        capture_output=True, text=True, check=False,
    )
    if inspect.returncode or inspect.stdout.strip() != expected_config_digest:
        raise RuntimeError("loaded image config digest differs from official manifest")
    return {"local_tag": tag, "loaded_config_digest": inspect.stdout.strip(), "docker_load_output": stdout.strip()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instance_id")
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--load", action="store_true")
    args = parser.parse_args()
    root = args.workdir.resolve() / "layout"
    result = build_layout(args.instance_id, root, timeout_seconds=args.timeout)
    if args.load:
        archive = args.workdir.resolve() / "docker_archive.tar"
        archive_layout(root, archive)
        result["load"] = load_archive(archive, result["config_digest"], result["local_tag"])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
