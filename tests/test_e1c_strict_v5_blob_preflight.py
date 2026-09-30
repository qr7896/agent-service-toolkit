import json

import evals.e1c_strict_v5_blob_preflight as preflight


def test_select_layer_uses_largest_real_layer() -> None:
    result = preflight._select_layer(
        {
            "layers": [
                {"digest": "sha256:" + "a" * 64, "size": 10},
                {"digest": "sha256:" + "b" * 64, "size": 50},
            ]
        }
    )
    assert result["digest"] == "sha256:" + "b" * 64


def test_platform_manifest_resolves_linux_amd64(monkeypatch) -> None:
    index = {
        "manifests": [
            {
                "digest": "sha256:" + "a" * 64,
                "platform": {"architecture": "amd64", "os": "linux"},
            },
            {
                "digest": "sha256:" + "b" * 64,
                "platform": {"architecture": "arm64", "os": "linux"},
            },
        ]
    }
    platform = {"layers": [{"digest": "sha256:" + "c" * 64, "size": 100}]}
    calls = []

    def fake_json_get(proxy, url, headers, timeout):
        calls.append(url)
        payload = index if url.endswith("/latest") else platform
        return payload, {"status": 200}

    monkeypatch.setattr(preflight, "_json_get", fake_json_get)
    payload, _ = preflight._platform_manifest(
        None, "swebench/example", "latest", "token", 5
    )
    assert payload == platform
    assert calls[-1].endswith("sha256:" + "a" * 64)


def test_probe_image_marks_slow_blob_not_ready(monkeypatch) -> None:
    layer = {"digest": "sha256:" + "d" * 64, "size": 10_000_000}
    monkeypatch.setattr(preflight, "_token", lambda proxy, repo, timeout: "token")
    monkeypatch.setattr(
        preflight,
        "_platform_manifest",
        lambda *args, **kwargs: ({"layers": [layer]}, {"status": 200}),
    )
    monkeypatch.setattr(
        preflight,
        "_probe_blob",
        lambda *args, **kwargs: {
            "status": 206,
            "bytes_read": 100_000,
            "sample_bytes": 1_000_000,
            "duration_seconds": 30,
            "bytes_per_second": 3333,
            "range_requested": True,
            "sample_sha256": "x",
        },
    )
    result = preflight.probe_image("swebench/example:latest")
    assert result["ready"] is False
    assert result["reason"] == "blob_transport_too_slow"


def test_probe_image_rejects_transport_that_exceeds_pull_budget(monkeypatch) -> None:
    layers = [
        {"digest": "sha256:" + "d" * 64, "size": 900_000_000},
        {"digest": "sha256:" + "e" * 64, "size": 300_000_000},
    ]
    monkeypatch.setattr(preflight, "_token", lambda proxy, repo, timeout: "token")
    monkeypatch.setattr(
        preflight,
        "_platform_manifest",
        lambda *args, **kwargs: ({"layers": layers}, {"status": 200}),
    )
    monkeypatch.setattr(
        preflight,
        "_probe_blob",
        lambda *args, **kwargs: {
            "status": 200,
            "bytes_read": 1_048_576,
            "sample_bytes": 1_048_576,
            "duration_seconds": 4,
            "bytes_per_second": 262_144,
            "range_requested": True,
            "sample_sha256": "x",
        },
    )
    result = preflight.probe_image(
        "swebench/example:latest",
        max_estimated_seconds=900,
    )
    assert result["ready"] is False
    assert result["reason"] == "blob_transport_exceeds_pull_budget"
    assert result["total_layer_bytes"] == 1_200_000_000
    assert result["estimated_full_image_seconds"] > 900


def test_run_stops_after_first_failed_transport(tmp_path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
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
    monkeypatch.setattr(preflight, "MANIFEST", manifest)
    calls = []

    def fake_probe(image, **kwargs):
        calls.append(image)
        return {"image": image, "ready": False, "reason": "blob_transport_too_slow"}

    monkeypatch.setattr(preflight, "probe_image", fake_probe)
    result = preflight.run(output=tmp_path / "out.json", ledger=None)
    assert result["ready"] is False
    assert result["checked_count"] == 1
    assert calls == ["swebench/a:latest"]


def test_run_appends_bounded_evidence_without_proxy_value(tmp_path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {"tasks": [{"instance_id": "a__one", "image": "swebench/a:latest"}]}
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(preflight, "MANIFEST", manifest)
    monkeypatch.setattr(
        preflight,
        "probe_image",
        lambda image, **kwargs: {
            "image": image,
            "ready": False,
            "reason": "blob_transport_exceeds_pull_budget",
            "blob_probe": {"bytes_per_second": 250_000},
            "total_layer_bytes": 2_000_000_000,
            "estimated_full_image_seconds": 8000.0,
        },
    )
    ledger = tmp_path / "ledger.jsonl"
    result = preflight.run(
        proxy="http://127.0.0.1:7892",
        output=tmp_path / "out.json",
        ledger=ledger,
    )
    row = json.loads(ledger.read_text(encoding="utf-8").strip())
    assert result["ready"] is False
    assert row["network_exit"] == {
        "explicit_proxy": True,
        "proxy_value_recorded": False,
    }
    assert "127.0.0.1" not in ledger.read_text(encoding="utf-8")


def test_probe_blob_reads_at_most_requested_sample(monkeypatch) -> None:
    payload = b"x" * 4096
    monkeypatch.setattr(preflight, "_curl", lambda *args, **kwargs: payload)
    values = iter([1.0, 2.0])
    monkeypatch.setattr(preflight.time, "monotonic", lambda: next(values))
    result = preflight._probe_blob(
        None,
        "swebench/example",
        "sha256:" + "a" * 64,
        "token",
        sample_bytes=1024,
        timeout=5,
    )
    assert result["bytes_read"] == 1024
    assert result["bytes_per_second"] == 1024.0


def test_partial_transfer_counts_extracts_curl_timeout_progress() -> None:
    detail = (
        "curl: (28) Operation timed out after 30331 milliseconds "
        "with 162535 out of 1048576 bytes received"
    )
    assert preflight._partial_transfer_counts(detail) == (162535, 1048576)


def test_curl_failure_carries_partial_transfer_metadata(monkeypatch) -> None:
    class Completed:
        returncode = 28
        stdout = b""
        stderr = (
            b"curl: (28) Operation timed out after 30331 milliseconds "
            b"with 162535 out of 1048576 bytes received"
        )

    monkeypatch.setattr(preflight.shutil, "which", lambda name: "curl")
    monkeypatch.setattr(preflight.subprocess, "run", lambda *args, **kwargs: Completed())
    try:
        preflight._curl(
            "http://proxy.invalid",
            "https://example.invalid/blob",
            {},
            30,
            byte_range="0-1048575",
        )
    except preflight.CurlTransferError as exc:
        assert exc.partial_bytes_received == 162535
        assert exc.requested_bytes == 1048576
    else:
        raise AssertionError("expected CurlTransferError")
