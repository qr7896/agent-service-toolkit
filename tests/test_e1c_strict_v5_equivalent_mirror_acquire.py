from types import SimpleNamespace

import evals.e1c_strict_v5_equivalent_mirror_acquire as mirror


def _identity(digest: str) -> dict:
    return {
        "mirror_transport_ready": True,
        "rows": [
            {
                "instance_id": "repo__one",
                "official_image": "swebench/example:latest",
                "mirror_image": "ghcr.io/example:latest",
                "authoritative_digest": digest,
            }
        ],
    }


def test_mirror_acquisition_refuses_unproven_equivalence(tmp_path) -> None:
    result = mirror.acquire(
        {"mirror_transport_ready": False, "rows": []},
        output=tmp_path / "out.json",
    )
    assert result["ready"] is False
    assert result["reason"] == "mirror_transport_not_digest_proven"
    assert result["pull_attempted"] is False


def test_mirror_acquisition_tags_only_after_exact_digest_match(
    tmp_path, monkeypatch
) -> None:
    digest = "sha256:" + "a" * 64
    calls = []

    def fake_repo_digest(image):
        return image.split(":", 1)[0] + "@" + digest

    def fake_run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(mirror, "_repo_digest", fake_repo_digest)
    monkeypatch.setattr(mirror.subprocess, "run", fake_run)
    result = mirror.acquire(_identity(digest), output=tmp_path / "out.json")
    assert result["ready"] is True
    assert result["pull_attempted"] is False
    assert calls == [
        ["docker", "tag", "ghcr.io/example:latest", "swebench/example:latest"]
    ]


def test_mirror_acquisition_stops_on_digest_mismatch(tmp_path, monkeypatch) -> None:
    expected = "sha256:" + "a" * 64
    wrong = "sha256:" + "b" * 64
    monkeypatch.setattr(
        mirror,
        "_repo_digest",
        lambda image: image.split(":", 1)[0] + "@" + wrong,
    )
    monkeypatch.setattr(
        mirror.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    result = mirror.acquire(_identity(expected), output=tmp_path / "out.json")
    assert result["ready"] is False
    assert result["reason"] == "equivalent_mirror_acquisition_incomplete"
    assert result["rows"][0]["mirror_digest_match"] is False
