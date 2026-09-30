import hashlib
import json
from types import SimpleNamespace

import evals.e1c_strict_v5_official_image_acquire as acquire


def test_remote_manifest_hashes_official_index_and_selects_linux_amd64(monkeypatch):
    raw = json.dumps({"manifests": [
        {"digest": "sha256:" + "a" * 64, "platform": {"architecture": "amd64", "os": "linux"}},
        {"digest": "sha256:" + "b" * 64, "platform": {"architecture": "unknown", "os": "unknown"}},
    ]}).encode()

    def fake_run(command, **kwargs):
        assert command[:5] == ["docker", "buildx", "imagetools", "inspect", "--raw"]
        return SimpleNamespace(returncode=0, stdout=raw, stderr=b"")

    monkeypatch.setattr(acquire.subprocess, "run", fake_run)
    result = acquire._remote_manifest("swebench/example:latest")
    assert result["ready"] is True
    assert result["digest"] == "sha256:" + hashlib.sha256(raw).hexdigest()
    assert result["platform_digest"] == "sha256:" + "a" * 64


def test_remote_manifest_rejects_ambiguous_platform(monkeypatch):
    raw = json.dumps({"manifests": [
        {"digest": "sha256:" + "a" * 64, "platform": {"architecture": "amd64", "os": "linux"}},
        {"digest": "sha256:" + "b" * 64, "platform": {"architecture": "amd64", "os": "linux"}},
    ]}).encode()
    monkeypatch.setattr(
        acquire.subprocess, "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=raw, stderr=b""),
    )
    assert acquire._remote_manifest("swebench/example:latest")["ready"] is False


def test_remote_manifest_checks_single_image_config_platform(monkeypatch):
    raw = json.dumps({"schemaVersion": 2, "mediaType": "application/vnd.docker.distribution.manifest.v2+json"}).encode()
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        stdout = raw if "--raw" in command else json.dumps({
            "manifest": {"digest": digest},
            "image": {"architecture": "amd64", "os": "linux"},
        }).encode()
        return SimpleNamespace(returncode=0, stdout=stdout, stderr=b"")

    monkeypatch.setattr(acquire.subprocess, "run", fake_run)
    result = acquire._remote_manifest("swebench/example:latest")
    assert result["ready"] is True
    assert result["digest"] == digest
    assert len(calls) == 2


def _manifest(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "tasks": [
                    {"instance_id": "a__one", "image": "swebench/a:latest"},
                    {"instance_id": "b__two", "image": "swebench/b:latest"},
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def test_acquisition_stops_before_pull_if_manifest_preflight_incomplete(tmp_path, monkeypatch):
    monkeypatch.setattr(acquire, "MANIFEST", _manifest(tmp_path))
    monkeypatch.setattr(
        acquire,
        "_remote_manifest",
        lambda image: {
            "ready": image.endswith("a:latest"),
            "digest": "sha256:" + "a" * 64 if image.endswith("a:latest") else None,
        },
    )
    monkeypatch.setattr(
        acquire.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("pull must not start")),
    )
    result = acquire.acquire(output=tmp_path / "out.json")
    assert result["ready"] is False
    assert result["reason"] == "official_manifest_preflight_incomplete"
    assert result["pull_attempted"] is False


def test_acquisition_accepts_existing_exact_digest_without_pull(tmp_path, monkeypatch):
    monkeypatch.setattr(acquire, "MANIFEST", _manifest(tmp_path))
    digest = "sha256:" + "a" * 64
    monkeypatch.setattr(
        acquire,
        "_remote_manifest",
        lambda image: {"ready": True, "digest": digest, "platform": {"architecture": "amd64", "os": "linux"}},
    )
    monkeypatch.setattr(
        acquire,
        "_local_repo_digest",
        lambda image: image.split(":", 1)[0] + "@" + digest,
    )
    result = acquire.acquire(output=tmp_path / "out.json")
    assert result["ready"] is True
    assert result["pull_attempted"] is False
    assert all(row["digest_match"] for row in result["rows"])


def test_acquisition_stops_after_first_failed_digest_match(tmp_path, monkeypatch):
    monkeypatch.setattr(acquire, "MANIFEST", _manifest(tmp_path))
    digest = "sha256:" + "a" * 64
    monkeypatch.setattr(
        acquire,
        "_remote_manifest",
        lambda image: {"ready": True, "digest": digest, "platform": {"architecture": "amd64", "os": "linux"}},
    )
    monkeypatch.setattr(acquire, "_local_repo_digest", lambda image: None)

    class Completed:
        returncode = 0

    monkeypatch.setattr(acquire.subprocess, "run", lambda *args, **kwargs: Completed())
    result = acquire.acquire(output=tmp_path / "out.json")
    assert result["ready"] is False
    assert len(result["rows"]) == 1
    assert result["rows"][0]["digest_match"] is False
