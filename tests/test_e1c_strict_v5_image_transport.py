import subprocess

import evals.e1c_strict_v5_image_transport as transport


def test_manifest_records_transport_failure_without_digest(monkeypatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 1, stdout="", stderr="connection reset"
        ),
    )
    result = transport._manifest("example/image:latest")
    assert result["reachable"] is False
    assert result["status"] == "transport_error"
    assert result["digest"] is None


def test_manifest_extracts_descriptor_without_layer_payload(monkeypatch) -> None:
    stdout = (
        '{"Descriptor":{"mediaType":"application/vnd.docker.distribution.manifest.v2+json",'
        '"digest":"sha256:' + "a" * 64 + '","platform":{"architecture":"amd64","os":"linux"}}}'
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, stdout=stdout, stderr=""),
    )
    result = transport._manifest("example/image:latest")
    assert result["reachable"] is True
    assert result["digest"] == "sha256:" + "a" * 64
    assert result["platform"]["architecture"] == "amd64"
