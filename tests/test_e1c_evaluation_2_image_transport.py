import hashlib
import json

from evals import e1c_evaluation_2_image_transport as transport


def test_manifest_selects_and_verifies_linux_amd64(monkeypatch):
    child = json.dumps({"layers": [{"size": 3, "digest": "sha256:" + "a" * 64}]}).encode()
    child_digest = "sha256:" + hashlib.sha256(child).hexdigest()
    index = json.dumps({"manifests": [
        {"platform": {"os": "linux", "architecture": "arm64"}, "digest": "sha256:" + "b" * 64},
        {"platform": {"os": "linux", "architecture": "amd64"}, "digest": child_digest},
    ]}).encode()
    monkeypatch.setattr(transport, "_token", lambda *args, **kwargs: "test-token")

    def fake_get(url, *, proxy, token=None):
        assert proxy is None and token == "test-token"
        return index if url.endswith("/latest") else child

    monkeypatch.setattr(transport, "_get", fake_get)
    result = transport._manifest("swebench/sweb.eval.x86_64.example", mirror=True, proxy=None)
    assert result["top_digest"] == "sha256:" + hashlib.sha256(index).hexdigest()
    assert result["platform_digest"] == child_digest
    assert result["compressed_layer_bytes"] == 3


def test_audit_binds_identity_and_never_requests_blobs(monkeypatch, tmp_path):
    task = {"instance_id": "example__example-1", "image": "swebench/sweb.eval.x86_64.example:latest"}
    metadata = {
        "schema": "e1c-evaluation-2-dev12-official-metadata-v1",
        "identity_sha256": hashlib.sha256(transport.IDENTITY.read_bytes()).hexdigest(),
        "tasks": [dict(task, instance_id=f"example__example-{n}") for n in range(12)],
    }
    source = tmp_path / "metadata.json"
    source.write_text(json.dumps(metadata), encoding="utf-8")
    calls = []

    def fake_manifest(repository, *, mirror, proxy, mirror_host):
        calls.append((repository, mirror, proxy, mirror_host))
        return {"top_digest": "sha256:" + "a" * 64, "platform_digest": "sha256:" + "b" * 64}

    monkeypatch.setattr(transport, "_manifest", fake_manifest)
    result = transport.audit(source, tmp_path / "transport.json", official_metadata_proxy="http://127.0.0.1:7892")
    assert result["digest_identical_count"] == 12
    assert result["blob_requests"] == result["image_pulls"] == result["provider_calls"] == 0
    assert calls[0][1:] == (False, "http://127.0.0.1:7892", "docker.1ms.run")
    assert calls[1][1:] == (True, None, "docker.1ms.run")
