from copy import deepcopy
from dataclasses import replace

from evals.e1b_experiment_admission_v10_7 import AdmissionConfig, admit
from evals.e1b_freeze_manifest_v10_6 import EXCLUDED_SOURCES, content_manifest


def valid_config():
    return AdmissionConfig(
        task_metadata={
            "task_count": 12,
            "repo_ids": ["public-repo-a"],
            "commit_ids": ["abc1234"],
            "curation_timestamps": ["2026-09-20T00:00:00Z"],
            "overlap_audit_passed": True,
            "source_commit_overlap": False,
            "manifest_sha256": "a" * 64,
            "base_fail_attested": True,
            "gold_pass_independently_attested": True,
        },
        data_isolation=EXCLUDED_SOURCES,
        frozen_identifiers={
            "model_id": "provider/model-v1",
            "editor_prompt_sha256": "b" * 64,
            "runtime_sha256": "c" * 64,
            "retrieval_policy_sha256": "d" * 64,
            "tool_config_sha256": "e" * 64,
            "sandbox_config_sha256": "f" * 64,
            "analysis_script_sha256": "1" * 64,
            "experiment_arm_id": "adaptive-acquisition",
        },
        provider_call_ceiling=24,
        provider_token_ceiling=100000,
        one_shot_frozen=True,
    )


def test_valid_case_is_offline_ready_only():
    result = admit(valid_config())
    assert result["decision"] == "ADMIT_OFFLINE_READY"
    assert result["starts_experiment"] is False
    assert result["reason_codes"] == ["all_admission_checks_passed"]


def test_deterministic_result():
    assert admit(valid_config()) == admit(valid_config())


def test_freeze_tamper_rejected():
    manifest = deepcopy(content_manifest())
    manifest["bounds"]["max_escalations"] += 1
    assert "freeze_manifest_invalid" in admit(valid_config(), manifest)["reason_codes"]


def test_forbidden_metadata_rejected():
    config = valid_config()
    config.task_metadata["issue_text"] = "hidden"
    assert "forbidden_task_metadata" in admit(config)["reason_codes"]


def test_overlap_rejected():
    config = valid_config()
    config.task_metadata["source_commit_overlap"] = True
    assert "overlap_audit_failed" in admit(config)["reason_codes"]


def test_missing_attestation_rejected():
    config = valid_config()
    config.task_metadata["base_fail_attested"] = False
    assert "heldout_attestation_missing" in admit(config)["reason_codes"]


def test_secret_like_identifier_field_rejected():
    config = valid_config()
    config.frozen_identifiers["api_key"] = "do-not-store"
    assert "secret_like_identifier_field" in admit(config)["reason_codes"]


def test_invalid_identifier_rejected():
    config = valid_config()
    config.frozen_identifiers["runtime_sha256"] = ""
    assert "frozen_identifier_invalid" in admit(config)["reason_codes"]


def test_budget_and_one_shot_rejected():
    config = replace(valid_config(), provider_call_ceiling=0, one_shot_frozen=False)
    reasons = admit(config)["reason_codes"]
    assert "provider_budget_invalid" in reasons
    assert "config_not_one_shot_frozen" in reasons


def test_data_isolation_mismatch_rejected():
    config = replace(valid_config(), data_isolation=EXCLUDED_SOURCES[:-1])
    assert "data_isolation_mismatch" in admit(config)["reason_codes"]


def test_runtime_feature_leakage_rejected():
    config = replace(valid_config(), runtime_features=({"nested": {"expected_patch": "x"}},))
    assert "runtime_feature_leakage" in admit(config)["reason_codes"]
