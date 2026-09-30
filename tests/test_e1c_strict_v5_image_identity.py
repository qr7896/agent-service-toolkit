import json
from types import SimpleNamespace

import evals.e1c_strict_v5_image_identity as identity


def test_consensus_requires_exact_agreement() -> None:
    a = "sha256:" + "a" * 64
    b = "sha256:" + "b" * 64
    assert identity._consensus(None, None) == (None, "authoritative_digest_unavailable")
    assert identity._consensus(a, a) == (a, "authoritative_digest_consensus")
    assert identity._consensus(a, b) == (None, "authoritative_digest_conflict")


def test_tag_api_extracts_single_linux_amd64_digest(monkeypatch) -> None:
    digest = "sha256:" + "a" * 64
    payload = {
        "digest": digest,
        "images": [
            {"architecture": "amd64", "os": "linux", "digest": digest},
            {"architecture": "unknown", "os": "unknown", "digest": "sha256:" + "b" * 64},
        ],
    }
    monkeypatch.setattr(identity.shutil, "which", lambda name: "curl")
    monkeypatch.setattr(
        identity.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0, stdout=json.dumps(payload), stderr=""
        ),
    )
    result = identity._dockerhub_tag_api("swebench/example:latest")
    assert result["ready"] is True
    assert result["digest"] == digest
    assert result["platform_count"] == 1


def test_tag_api_transport_error_is_not_authoritative(monkeypatch) -> None:
    monkeypatch.setattr(identity.shutil, "which", lambda name: "curl")
    monkeypatch.setattr(
        identity.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=28, stdout="", stderr="connection timed out"
        ),
    )
    result = identity._dockerhub_tag_api("swebench/example:latest")
    assert result["ready"] is False
    assert result["status"] == "tag_api_transport_error"
    assert "digest" not in result


def test_registry_v2_digest_uses_exact_platform_manifest_body_sha(monkeypatch) -> None:
    body_sha = "a" * 64
    monkeypatch.setattr(
        identity,
        "_token",
        lambda proxy, repository, timeout: "token",
    )
    monkeypatch.setattr(
        identity,
        "_platform_manifest",
        lambda proxy, repository, reference, token, timeout: (
            {"layers": []},
            {"sha256": body_sha, "bytes": 1234},
        ),
    )
    result = identity._dockerhub_registry_digest(
        "swebench/example:latest",
        proxy="http://proxy.invalid",
    )
    assert result["ready"] is True
    assert result["digest"] == "sha256:" + body_sha
    assert result["manifest_bytes"] == 1234


def test_build_only_admits_mirror_on_exact_authoritative_digest(
    tmp_path, monkeypatch
) -> None:
    digest = "sha256:" + "a" * 64
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "instance_id": "repo__one",
                        "image": "swebench/example:latest",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    transport = tmp_path / "transport.json"
    transport.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "instance_id": "repo__one",
                        "official": {"reachable": False, "digest": None},
                        "mirror_image": "ghcr.io/example:latest",
                        "mirror": {
                            "reachable": True,
                            "digest": digest,
                            "platform": {"architecture": "amd64", "os": "linux"},
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(identity, "MANIFEST", manifest)
    monkeypatch.setattr(identity, "TRANSPORT", transport)
    monkeypatch.setattr(
        identity,
        "_dockerhub_tag_api",
        lambda image, timeout=8, proxy=None: {"ready": True, "digest": digest},
    )
    monkeypatch.setattr(
        identity,
        "_dockerhub_registry_digest",
        lambda image, timeout=12, proxy=None: {"ready": True, "digest": digest},
    )
    result = identity.build(output=tmp_path / "out.json")
    assert result["ready"] is True
    assert result["mirror_transport_ready"] is True
    assert result["rows"][0]["mirror_transport_admissible"] is True


def test_build_rejects_mirror_digest_mismatch(tmp_path, monkeypatch) -> None:
    official = "sha256:" + "a" * 64
    mirror = "sha256:" + "b" * 64
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {"tasks": [{"instance_id": "repo__one", "image": "swebench/example:latest"}]}
        ),
        encoding="utf-8",
    )
    transport = tmp_path / "transport.json"
    transport.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "instance_id": "repo__one",
                        "official": {"reachable": False, "digest": None},
                        "mirror_image": "ghcr.io/example:latest",
                        "mirror": {
                            "reachable": True,
                            "digest": mirror,
                            "platform": {"architecture": "amd64", "os": "linux"},
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(identity, "MANIFEST", manifest)
    monkeypatch.setattr(identity, "TRANSPORT", transport)
    monkeypatch.setattr(
        identity,
        "_dockerhub_tag_api",
        lambda image, timeout=8, proxy=None: {"ready": True, "digest": official},
    )
    monkeypatch.setattr(
        identity,
        "_dockerhub_registry_digest",
        lambda image, timeout=12, proxy=None: {"ready": True, "digest": official},
    )
    result = identity.build(output=tmp_path / "out.json")
    assert result["ready"] is True
    assert result["mirror_transport_ready"] is False
    assert result["rows"][0]["mirror_transport_admissible"] is False


def test_build_rejects_conflicting_registry_and_tag_api_digests(
    tmp_path, monkeypatch
) -> None:
    registry = "sha256:" + "a" * 64
    tag_api = "sha256:" + "b" * 64
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {"tasks": [{"instance_id": "repo__one", "image": "swebench/example:latest"}]}
        ),
        encoding="utf-8",
    )
    transport = tmp_path / "transport.json"
    transport.write_text(json.dumps({"rows": []}), encoding="utf-8")
    monkeypatch.setattr(identity, "MANIFEST", manifest)
    monkeypatch.setattr(identity, "TRANSPORT", transport)
    monkeypatch.setattr(
        identity,
        "_dockerhub_registry_digest",
        lambda image, timeout=12, proxy=None: {"ready": True, "digest": registry},
    )
    monkeypatch.setattr(
        identity,
        "_dockerhub_tag_api",
        lambda image, timeout=8, proxy=None: {"ready": True, "digest": tag_api},
    )
    result = identity.build(output=tmp_path / "out.json")
    assert result["ready"] is False
    assert result["rows"][0]["identity_status"] == "authoritative_digest_conflict"
