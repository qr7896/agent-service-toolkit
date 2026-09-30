import json
from types import SimpleNamespace

import evals.e1c_strict_v5_cache_accounting as cache


def test_account_maps_compressed_layers_to_diff_ids() -> None:
    manifest = {
        "layers": [
            {"digest": "sha256:" + "a" * 64, "size": 100},
            {"digest": "sha256:" + "b" * 64, "size": 300},
        ]
    }
    config = {
        "rootfs": {
            "diff_ids": [
                "sha256:" + "c" * 64,
                "sha256:" + "d" * 64,
            ]
        }
    }
    result = cache._account(
        manifest,
        config,
        {"sha256:" + "c" * 64},
    )
    assert result["layer_count"] == 2
    assert result["cached_layer_count"] == 1
    assert result["total_compressed_bytes"] == 400
    assert result["cached_compressed_bytes"] == 100
    assert result["remaining_compressed_bytes"] == 300
    assert result["cached_compressed_fraction"] == 0.25


def test_account_fails_closed_on_layer_count_mismatch() -> None:
    try:
        cache._account(
            {"layers": [{"digest": "sha256:" + "a" * 64, "size": 100}]},
            {"rootfs": {"diff_ids": []}},
            set(),
        )
    except RuntimeError as exc:
        assert str(exc) == "manifest_config_layer_count_mismatch"
    else:
        raise AssertionError("expected mismatch failure")


def test_local_diff_ids_reads_all_local_images(monkeypatch) -> None:
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        if args[:4] == ["docker", "image", "ls", "-q"]:
            return SimpleNamespace(returncode=0, stdout="sha256:1\nsha256:2\n", stderr="")
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                [
                    {"RootFS": {"Layers": ["sha256:" + "a" * 64]}},
                    {"RootFS": {"Layers": ["sha256:" + "b" * 64]}},
                ]
            ),
            stderr="",
        )

    monkeypatch.setattr(cache.subprocess, "run", fake_run)
    result = cache._local_diff_ids()
    assert result == {"sha256:" + "a" * 64, "sha256:" + "b" * 64}
    assert calls[1][:3] == ["docker", "image", "inspect"]


def test_build_is_diagnostic_only(tmp_path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {"tasks": [{"instance_id": "a__one", "image": "swebench/a:latest"}]}
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(cache, "MANIFEST", manifest)
    monkeypatch.setattr(cache, "_local_diff_ids", lambda timeout=20: {"sha256:" + "a" * 64})
    monkeypatch.setattr(
        cache,
        "inspect_image",
        lambda image, **kwargs: {
            "image": image,
            "ready": True,
            "remaining_compressed_bytes": 123,
        },
    )
    result = cache.build(output=tmp_path / "out.json")
    assert result["ready_count"] == 1
    assert result["diagnostic_only"] is True
    assert result["changes_admission_gate"] is False
    assert result["c5_allowed"] is False
    assert result["fresh30_allowed"] is False
