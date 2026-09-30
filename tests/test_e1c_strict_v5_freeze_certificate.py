import json

from evals.e1c_strict_v5_freeze_certificate import certify


def _manifest() -> dict:
    return {
        "schema": "e1c-strict-v5-external-canary-reserve-v1",
        "source": "external_disjoint_canary_reserve",
        "source_revision": "rev-1",
        "identity_frozen_before_statement_materialization": True,
        "tasks": [
            {"instance_id": "new-aa", "repo": "o/r", "base_commit": "a" * 40, "image": "img:a"},
            {"instance_id": "new-bb", "repo": "o/r", "base_commit": "b" * 40, "image": "img:b"},
            {"instance_id": "new-cc", "repo": "o/r", "base_commit": "c" * 40, "image": "img:c"},
        ],
    }


def test_certificate_accepts_clean_synthetic_identity(tmp_path) -> None:
    manifest = tmp_path / "manifest.json"
    audit = tmp_path / "audit.json"
    manifest.write_text(json.dumps(_manifest()), encoding="utf-8")
    audit.write_text(json.dumps({
        "provider_calls": 0,
        "task_content_inspected": False,
        "source_revision": "rev-1",
        "eligible": _manifest()["tasks"],
    }), encoding="utf-8")
    result = certify(manifest, audit, output=None)
    assert result["ready"] is True
    assert result["checks"]["freeze_rows_match_audit_snapshot"] is True


def test_certificate_fails_on_revision_mismatch(tmp_path) -> None:
    manifest = tmp_path / "manifest.json"
    audit = tmp_path / "audit.json"
    manifest.write_text(json.dumps(_manifest()), encoding="utf-8")
    audit.write_text(json.dumps({
        "provider_calls": 0,
        "task_content_inspected": False,
        "source_revision": "different",
        "eligible": _manifest()["tasks"],
    }), encoding="utf-8")
    result = certify(manifest, audit, output=None)
    assert result["ready"] is False
    assert result["checks"]["audit_source_revision_matches"] is False
