import json

from evals.e1b_experiment_package_v10_8 import REQUIRED_ARTIFACTS
from evals.e1b_replacement_preflight import run


def write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def metadata(valid=True):
    return {
        "task_count": 2 if valid else 0,
        "repo_ids": ["repo"], "commit_ids": ["abc1234"],
        "curation_timestamps": ["2026-09-20T00:00:00Z"],
        "overlap_audit_passed": True, "source_commit_overlap": False,
        "manifest_sha256": "a" * 64, "base_fail_attested": True,
        "gold_pass_independently_attested": True,
    }


def config():
    return {
        "frozen_identifiers": {
            "model_id": "provider/model-v1", "editor_prompt_sha256": "b" * 64,
            "runtime_sha256": "c" * 64, "retrieval_policy_sha256": "d" * 64,
            "tool_config_sha256": "e" * 64, "sandbox_config_sha256": "f" * 64,
            "analysis_script_sha256": "1" * 64,
            "experiment_arm_id": "adaptive-acquisition",
        },
        "provider_call_ceiling": 2, "provider_token_ceiling": 100,
        "one_shot_frozen": True, "runtime_features": [],
    }


def test_real_metadata_path_materializes_only_dry_run_artifacts(tmp_path):
    meta = tmp_path / "metadata.json"
    cfg = tmp_path / "config.json"
    output = tmp_path / "dry-run"
    write(meta, metadata())
    write(cfg, config())
    result = run(meta, cfg, output)
    assert result["status"] == "READY_FOR_DRY_RUN_AUDIT"
    assert result["provider_calls"] == 0
    assert result["starts_experiment"] is False
    assert {path.name for path in output.iterdir()} == set(REQUIRED_ARTIFACTS)


def test_invalid_metadata_rejects_without_materializing(tmp_path):
    meta = tmp_path / "metadata.json"
    cfg = tmp_path / "config.json"
    output = tmp_path / "dry-run"
    write(meta, metadata(valid=False))
    write(cfg, config())
    result = run(meta, cfg, output)
    assert result["status"] == "REJECT"
    assert result["provider_calls"] == 0
    assert not output.exists()
