import json

import evals.e1c_strict_v5_direct_oci_plan as plan


def test_build_keeps_direct_oci_plan_diagnostic_only(tmp_path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {"tasks": [{"instance_id": "a__one", "image": "swebench/a:latest"}]}
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(plan, "MANIFEST", manifest)
    monkeypatch.setattr(
        plan,
        "plan_image",
        lambda image, **kwargs: {
            "image": image,
            "remaining_compressed_bytes": 900_000_000,
        },
    )
    result = plan.build(output=tmp_path / "out.json", pull_timeout=900)
    assert result["diagnostic_only"] is True
    assert result["changes_admission_gate"] is False
    assert result["rows"][0]["required_bytes_per_second_for_budget"] == 1_000_000
    assert result["c5_allowed"] is False


def test_plan_image_counts_only_uncached_layers(monkeypatch) -> None:
    monkeypatch.setattr(plan, "_token", lambda proxy, repository, timeout: "token")
    monkeypatch.setattr(
        plan,
        "_platform_manifest",
        lambda *args, **kwargs: (
            {
                "layers": [
                    {"digest": "sha256:" + "a" * 64, "size": 100},
                    {"digest": "sha256:" + "b" * 64, "size": 300},
                ]
            },
            {"sha256": "c" * 64, "bytes": 123},
        ),
    )
    monkeypatch.setattr(
        plan,
        "_config",
        lambda *args, **kwargs: (
            {
                "rootfs": {
                    "diff_ids": [
                        "sha256:" + "d" * 64,
                        "sha256:" + "e" * 64,
                    ]
                }
            },
            {"sha256": "f" * 64, "bytes": 45},
        ),
    )
    monkeypatch.setattr(plan, "_local_diff_ids", lambda timeout: {"sha256:" + "d" * 64})
    result = plan.plan_image(
        "swebench/a:latest",
        proxy=None,
        timeout=20,
    )
    assert result["remaining_layer_count"] == 1
    assert result["remaining_compressed_bytes"] == 300
    assert result["largest_remaining_layer_bytes"] == 300
