import gzip
import hashlib
import io
import json
import tarfile
import time
from types import SimpleNamespace

import pytest

from evals import e1c_evaluation_2_mirror_acquire as acquire


def test_direct_blob_is_hashed_and_reused(tmp_path, monkeypatch):
    payload = b"verified mirror bytes"
    digest = "sha256:" + hashlib.sha256(payload).hexdigest()
    calls = []

    class Response(io.BytesIO):
        status = 200
        headers = {}

    class Opener:
        def open(self, request, timeout):
            calls.append(request.full_url)
            assert request.get_header("User-agent") == "curl/8.0.1"
            return Response(payload)

    monkeypatch.setattr(acquire.urllib.request, "build_opener", lambda handler: Opener())
    descriptor = {"digest": digest, "size": len(payload)}
    first = acquire._download_blob("swebench/image", descriptor, tmp_path, time.monotonic() + 10)
    second = acquire._download_blob("swebench/image", descriptor, tmp_path, time.monotonic() + 10)
    assert first["reused"] is False and second["reused"] is True
    assert len(calls) == 1
    assert acquire._blob_path(tmp_path, digest).read_bytes() == payload


def test_direct_blob_mismatch_never_becomes_verified(tmp_path, monkeypatch):
    payload = b"wrong"
    digest = "sha256:" + hashlib.sha256(b"expected").hexdigest()

    class Response(io.BytesIO):
        status = 200
        headers = {}

    class Opener:
        def open(self, request, timeout):
            return Response(payload)

    monkeypatch.setattr(acquire.urllib.request, "build_opener", lambda handler: Opener())
    with pytest.raises(ValueError, match="differs from official descriptor"):
        acquire._download_blob("swebench/image", {"digest": digest, "size": len(payload)}, tmp_path, time.monotonic() + 10)
    assert not acquire._blob_path(tmp_path, digest).exists()


def test_direct_blob_resumes_only_at_exact_range(tmp_path, monkeypatch):
    payload = b"prefix-and-suffix"
    digest = "sha256:" + hashlib.sha256(payload).hexdigest()
    partial = acquire._blob_path(tmp_path, digest).with_name(digest[7:] + ".partial")
    partial.parent.mkdir(parents=True)
    partial.write_bytes(payload[:7])

    class Response(io.BytesIO):
        status = 206
        headers = {"Content-Range": f"bytes 7-{len(payload) - 1}/{len(payload)}", "Content-Length": str(len(payload) - 7)}

    class Opener:
        def open(self, request, timeout):
            assert request.get_header("Range") == "bytes=7-"
            return Response(payload[7:])

    monkeypatch.setattr(acquire.urllib.request, "build_opener", lambda handler: Opener())
    result = acquire._download_blob("swebench/image", {"digest": digest, "size": len(payload)}, tmp_path, time.monotonic() + 10)
    assert result["resumed_from_bytes"] == 7
    assert acquire._blob_path(tmp_path, digest).read_bytes() == payload
    assert not partial.exists()


def test_mirror_manifest_requires_official_digest(monkeypatch):
    raw = b'{"schemaVersion":2}'
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    monkeypatch.setattr(acquire, "_get", lambda url, proxy: raw)
    assert acquire._manifest("swebench/image", digest) == raw
    with pytest.raises(ValueError, match="differs from frozen official"):
        acquire._manifest("swebench/image", "sha256:" + "0" * 64)


def test_partial_transport_reconnect_is_bounded_and_never_retries_full_bad_blob(tmp_path, monkeypatch):
    digest = "sha256:" + "a" * 64
    descriptor = {"digest": digest, "size": 10}
    partial = acquire._blob_path(tmp_path, digest).with_name("a" * 64 + ".partial")
    partial.parent.mkdir(parents=True)
    monkeypatch.setattr(acquire.time, "sleep", lambda seconds: None)
    calls = []

    def interrupted(repository, item, root, deadline):
        calls.append(1)
        if len(calls) == 1:
            partial.write_bytes(b"abc")
            raise ValueError("early EOF")
        return {"reused": False}

    monkeypatch.setattr(acquire, "_download_blob", interrupted)
    assert acquire._download_blob_with_resume("swebench/image", descriptor, tmp_path, time.monotonic() + 10) == {"reused": False}
    assert len(calls) == 2
    calls.clear()
    partial.write_bytes(b"")

    def full_bad(repository, item, root, deadline):
        calls.append(1)
        partial.write_bytes(b"0123456789")
        raise ValueError("bad full digest")

    monkeypatch.setattr(acquire, "_download_blob", full_bad)
    with pytest.raises(ValueError, match="bad full digest"):
        acquire._download_blob_with_resume("swebench/image", descriptor, tmp_path, time.monotonic() + 10)
    assert len(calls) == 1


def test_verified_oci_layers_convert_to_docker_archive(tmp_path, monkeypatch):
    root = tmp_path / "layout"
    root.mkdir()
    raw_layer = b"example uncompressed tar bytes"
    compressed = gzip.compress(raw_layer)
    diff_id = "sha256:" + hashlib.sha256(raw_layer).hexdigest()
    layer_digest = "sha256:" + hashlib.sha256(compressed).hexdigest()
    config_raw = json.dumps({"rootfs": {"diff_ids": [diff_id]}}).encode()
    config_digest = "sha256:" + hashlib.sha256(config_raw).hexdigest()
    manifest_raw = json.dumps({
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {"digest": config_digest},
        "layers": [{"digest": layer_digest, "size": len(compressed), "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip"}],
    }).encode()
    manifest_digest = "sha256:" + hashlib.sha256(manifest_raw).hexdigest()
    for digest, value in ((config_digest, config_raw), (layer_digest, compressed), (manifest_digest, manifest_raw)):
        path = acquire._blob_path(root, digest)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    (root / "index.json").write_text(json.dumps({"manifests": [{
        "digest": manifest_digest, "annotations": {"org.opencontainers.image.ref.name": "e1c2/test:verified"},
    }]}), encoding="utf-8")
    monkeypatch.setattr(acquire.shutil, "disk_usage", lambda path: SimpleNamespace(free=100 * 1024**3))
    output = tmp_path / "docker_archive.tar"
    acquire.archive_layout(root, output)
    with tarfile.open(output) as archive:
        manifest = json.load(archive.extractfile("manifest.json"))[0]
        assert manifest["RepoTags"] == ["e1c2/test:verified"]
        assert archive.extractfile(manifest["Config"]).read() == config_raw
        assert archive.extractfile(manifest["Layers"][0]).read() == raw_layer
