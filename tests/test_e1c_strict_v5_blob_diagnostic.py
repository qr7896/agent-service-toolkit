import json

import pytest

import evals.e1c_strict_v5_blob_diagnostic as diagnostic


def _manifest(path):
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


def test_targeted_probe_only_accepts_frozen_instance(tmp_path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.json"
    _manifest(manifest)
    monkeypatch.setattr(diagnostic, "MANIFEST", manifest)
    monkeypatch.setattr(
        diagnostic,
        "probe_image",
        lambda image, **kwargs: {
            "image": image,
            "ready": True,
            "reason": "blob_transport_ready",
        },
    )
    result = diagnostic.run(
        "b__two",
        proxy="http://proxy.invalid",
        output=tmp_path / "out.json",
    )
    assert result["instance_id"] == "b__two"
    assert result["row"]["image"] == "swebench/b:latest"
    assert result["diagnostic_only"] is True
    assert result["changes_admission_gate"] is False
    assert result["formal_admission_ready"] is False
    assert result["c5_allowed"] is False
    assert result["fresh30_allowed"] is False
    assert "proxy.invalid" not in (tmp_path / "out.json").read_text(encoding="utf-8")


def test_targeted_probe_rejects_unknown_instance(tmp_path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.json"
    _manifest(manifest)
    monkeypatch.setattr(diagnostic, "MANIFEST", manifest)
    with pytest.raises(ValueError, match="instance_id_not_in_frozen_manifest"):
        diagnostic.run("c__three", output=tmp_path / "out.json")


def test_targeted_probe_does_not_claim_formal_readiness_on_success(
    tmp_path, monkeypatch
) -> None:
    manifest = tmp_path / "manifest.json"
    _manifest(manifest)
    monkeypatch.setattr(diagnostic, "MANIFEST", manifest)
    monkeypatch.setattr(
        diagnostic,
        "probe_image",
        lambda image, **kwargs: {
            "image": image,
            "ready": True,
            "reason": "blob_transport_ready",
            "estimated_full_image_seconds": 100.0,
        },
    )
    result = diagnostic.run("a__one", output=tmp_path / "out.json")
    assert result["ready_under_same_budget_estimate"] is True
    assert result["formal_admission_ready"] is False
    assert result["live_model_run"] is False
