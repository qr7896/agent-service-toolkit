import json
import urllib.request

import pytest

from evals import e1c_evaluation_2_canary_v2_metadata_proxy as proxy


def test_only_official_metadata_uses_local_proxy(monkeypatch):
    calls = []

    class Response:
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, size):
            return b"{}"

    class Opener:
        def open(self, request, timeout):
            calls[-1]["url"] = request.full_url
            calls[-1]["authorization"] = request.get_header("Authorization")
            return Response()

    def build(*handlers):
        handler = next(item for item in handlers if isinstance(item, urllib.request.ProxyHandler))
        assert any(isinstance(item, proxy._NoRedirect) for item in handlers)
        calls.append({"proxies": handler.proxies})
        return Opener()

    monkeypatch.setattr(proxy.urllib.request, "build_opener", build)
    client = proxy.MetadataClient()
    client.get("https://auth.docker.io/token?service=registry.docker.io")
    client.get("https://registry-1.docker.io/v2/swebench/sweb.eval.x86_64.example/manifests/latest", token="test-only-token")
    client.get("https://docker.1panel.live/v2/swebench/sweb.eval.x86_64.example/manifests/latest")
    assert [item["proxies"] for item in calls] == [{"https": proxy.PROXY}, {"https": proxy.PROXY}, {}]
    assert calls[-1]["authorization"] is None
    assert client.official_requests == 2 and client.official_bytes == 4
    assert client.mirror_requests == 1 and client.mirror_bytes == 2


def test_proxy_rejects_blob_unknown_host_and_redirect_before_fetch(monkeypatch):
    monkeypatch.setattr(proxy.urllib.request, "build_opener", lambda *args: pytest.fail("forbidden URL fetched"))
    client = proxy.MetadataClient()
    for url in (
        "https://registry-1.docker.io/v2/swebench/sweb.eval.x86_64.example/blobs/sha256:" + "a" * 64,
        "https://example.invalid/token", "http://auth.docker.io/token",
        "https://auth.docker.io:8443/token", "https://user@auth.docker.io/token",
    ):
        with pytest.raises(ValueError, match="metadata URLs"):
            client.get(url)
    with pytest.raises(ValueError, match="redirects"):
        proxy._NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.invalid/blob")
    assert client.official_requests == client.mirror_requests == 0


def test_metadata_limits_stop_before_large_body_or_more_requests(monkeypatch):
    class Response:
        headers = {"Content-Length": str(proxy.RESPONSE_CAP + 1)}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, size):
            pytest.fail("oversized advertised body must not be downloaded")

    class Opener:
        def open(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr(proxy.urllib.request, "build_opener", lambda *args: Opener())
    client = proxy.MetadataClient()
    with pytest.raises(ValueError, match="byte budget"):
        client.get("https://auth.docker.io/token")
    assert client.official_bytes == 0
    client.official_requests = proxy.OFFICIAL_REQUEST_CAP
    with pytest.raises(ValueError, match="budget exceeded"):
        client.get("https://auth.docker.io/token")


def test_manifest_mismatch_never_seals_and_success_reuses_seal(tmp_path, monkeypatch):
    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps({"tasks": [
        {"instance_id": f"example-{n}", "image": f"swebench/sweb.eval.x86_64.example_{n}:latest"}
        for n in range(3)
    ]}), encoding="utf-8")
    freeze, identity = tmp_path / "freeze.json", tmp_path / "identity.json"
    freeze.write_bytes(b"{}")
    identity.write_bytes(b"{}")
    monkeypatch.setattr(proxy, "METADATA", metadata)
    monkeypatch.setattr(proxy, "FREEZE", freeze)
    monkeypatch.setattr(proxy, "IDENTITY", identity)
    monkeypatch.setattr(proxy, "TRANSPORT", tmp_path / "seal.json")
    monkeypatch.setattr(proxy, "require_freeze", lambda: None)
    digest = {"top_digest": "sha256:" + "a" * 64, "platform_digest": "sha256:" + "b" * 64,
              "compressed_layer_bytes": 1000, "layer_count": 1}
    monkeypatch.setattr(proxy.MetadataClient, "manifest", lambda self, repo, official: {**digest, "layer_count": 1 if official else 2})
    with pytest.raises(ValueError, match="manifest differs"):
        proxy.audit()
    assert not proxy.TRANSPORT.exists()
    monkeypatch.setattr(proxy.MetadataClient, "manifest", lambda self, repo, official: digest)
    result = proxy.audit()
    assert len(result["rows"]) == 3 and result["provider_calls"] == result["blob_requests"] == 0
    monkeypatch.setattr(proxy.MetadataClient, "manifest", lambda *args, **kwargs: pytest.fail("sealed metadata fetched again"))
    assert proxy.audit() == result


def test_original_fourteen_method_files_remain_frozen():
    original = json.loads(proxy.ORIGINAL_FREEZE.read_bytes())
    assert len(original["method_files"]) == 14
    assert all(proxy._sha(proxy.ROOT / name) == digest for name, digest in original["method_files"].items())
