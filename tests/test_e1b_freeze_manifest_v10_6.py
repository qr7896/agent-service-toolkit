from copy import deepcopy

from evals.e1b_freeze_manifest_v10_6 import (
    EXCLUDED_SOURCES,
    REQUIRED_FILES,
    content_manifest,
    environment_metadata,
    verify_manifest,
)


def test_manifest_is_deterministic_and_covers_required_files():
    a = content_manifest()
    b = content_manifest()
    assert a == b
    assert set(a["files"]) == set(REQUIRED_FILES)


def test_tamper_detection_on_synthetic_manifest_copy():
    manifest = deepcopy(content_manifest())
    key = next(iter(manifest["files"]))
    manifest["files"][key] = "0" * 64
    result = verify_manifest(manifest)
    assert result == {"valid": False, "reason": "file_hash_mismatch"}


def test_schema_and_config_drift_fail_closed():
    manifest = deepcopy(content_manifest())
    manifest["schema_version"] = "wrong"
    assert verify_manifest(manifest)["reason"] == "schema_mismatch"
    manifest = deepcopy(content_manifest())
    manifest["bounds"]["max_escalations"] += 1
    assert verify_manifest(manifest)["reason"] == "config_drift"


def test_missing_file_fails_closed(tmp_path):
    result = verify_manifest(content_manifest(), root=tmp_path)
    assert result["valid"] is False
    assert result["reason"] == "missing_required_file"


def test_excluded_sources_are_explicit():
    manifest = content_manifest()
    assert tuple(manifest["excluded_sources"]) == EXCLUDED_SOURCES
    assert len(EXCLUDED_SOURCES) == 4


def test_environment_metadata_contains_no_secret_like_fields():
    metadata = environment_metadata()
    lowered = " ".join(metadata).lower()
    assert "key" not in lowered
    assert "token" not in lowered
    assert "secret" not in lowered
    assert "password" not in lowered


def test_environment_metadata_is_outside_stable_content_hash():
    manifest = content_manifest()
    assert "python_version" not in manifest
    assert "platform_system" not in manifest


def test_manifest_claim_boundary_and_offline_status():
    manifest = content_manifest()
    assert manifest["provider_calls"] == 0
    assert manifest["live_runner_exists"] is False
    assert "no repair efficacy claim" in manifest["claim_boundary"]
