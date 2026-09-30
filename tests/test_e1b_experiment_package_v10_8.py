import json
from dataclasses import replace

import pytest

from evals.e1b_experiment_admission_v10_7 import AdmissionConfig, admit
from evals.e1b_experiment_package_v10_8 import (
    REQUIRED_ARTIFACTS,
    audit_ledger,
    audit_metadata,
    build_package,
    dry_run_materialize,
    verify_package,
)
from evals.e1b_freeze_manifest_v10_6 import EXCLUDED_SOURCES


def config():
    return AdmissionConfig(
        task_metadata={"task_count": 2, "repo_ids": ["r"], "commit_ids": ["abc1234"], "curation_timestamps": ["2026-09-20"], "overlap_audit_passed": True, "source_commit_overlap": False, "manifest_sha256": "a" * 64, "base_fail_attested": True, "gold_pass_independently_attested": True},
        data_isolation=EXCLUDED_SOURCES,
        frozen_identifiers={"model_id": "provider/model-v1", "editor_prompt_sha256": "b" * 64, "runtime_sha256": "c" * 64, "retrieval_policy_sha256": "d" * 64, "tool_config_sha256": "e" * 64, "sandbox_config_sha256": "f" * 64, "analysis_script_sha256": "1" * 64, "experiment_arm_id": "adaptive-acquisition"},
        provider_call_ceiling=2, provider_token_ceiling=100, one_shot_frozen=True,
    )


def package():
    cfg = config()
    return build_package(admit(cfg), cfg)


def row(pkg, index=0, total=10):
    return {"schema_version": "e1b-provider-ledger-v1", "sequence": index + 1, "run_id": pkg["run_id"], "call_index": index, "model_id": pkg["frozen_identifiers"]["model_id"], "request_manifest_sha256": "2" * 64, "response_manifest_sha256": "3" * 64, "input_tokens": total - 2, "output_tokens": 2, "total_tokens": total, "status": "completed"}


def summary(pkg, calls=1, total=10):
    return {"run_id": pkg["run_id"], "provider_calls": calls, "total_tokens": total, "task_outcome_count": 2, "forbidden_source_accesses": 0, "package_manifest_sha256": pkg["package_manifest_sha256"]}


def test_package_and_run_id_are_deterministic():
    assert package() == package()


def test_rejected_admission_cannot_build():
    cfg = replace(config(), one_shot_frozen=False)
    with pytest.raises(ValueError):
        build_package(admit(cfg), cfg)


def test_dry_run_creates_metadata_only(tmp_path):
    pkg = package()
    result = dry_run_materialize(pkg, tmp_path)
    assert result["provider_calls"] == 0
    assert result["starts_experiment"] is False
    assert set(result["created_artifacts"]) == set(REQUIRED_ARTIFACTS)
    assert (tmp_path / "provider_calls.jsonl").read_text() == ""
    assert (tmp_path / "task_outcomes.jsonl").read_text() == ""
    assert json.loads((tmp_path / "run_summary.json").read_text())["dry_run"] is True


def test_valid_ledger_reconciles():
    pkg = package()
    result = audit_ledger(pkg, [row(pkg)], summary(pkg), REQUIRED_ARTIFACTS)
    assert result["valid"] is True


def test_nonmonotonic_and_wrong_identity_rejected():
    pkg = package()
    bad = row(pkg)
    bad["sequence"] = 9
    bad["run_id"] = "wrong"
    bad["model_id"] = "wrong"
    reasons = audit_ledger(pkg, [bad], summary(pkg), REQUIRED_ARTIFACTS)["reason_codes"]
    assert "ledger_index_nonmonotonic" in reasons
    assert "ledger_run_id_mismatch" in reasons
    assert "ledger_model_mismatch" in reasons


def test_budget_overflow_rejected():
    pkg = package()
    rows = [row(pkg, 0, 60), row(pkg, 1, 60)]
    assert "provider_budget_exceeded" in audit_ledger(pkg, rows, summary(pkg, 2, 120), REQUIRED_ARTIFACTS)["reason_codes"]


def test_missing_artifact_and_outcome_count_rejected():
    pkg = package()
    s = summary(pkg)
    s["task_outcome_count"] = 1
    reasons = audit_ledger(pkg, [row(pkg)], s, REQUIRED_ARTIFACTS[:-1])["reason_codes"]
    assert "missing_required_artifact" in reasons
    assert "task_outcome_count_mismatch" in reasons


def test_manifest_chain_drift_rejected():
    pkg = package()
    s = summary(pkg)
    s["package_manifest_sha256"] = "0" * 64
    assert "manifest_chain_drift" in audit_ledger(pkg, [row(pkg)], s, REQUIRED_ARTIFACTS)["reason_codes"]


def test_forbidden_metadata_rejected_recursively():
    with pytest.raises(ValueError):
        audit_metadata({"safe": {"prompt_text": "secret"}})


def test_package_tamper_is_detected_and_dry_run_refuses_it(tmp_path):
    pkg = package()
    pkg["provider_call_ceiling"] += 1
    assert verify_package(pkg)["valid"] is False
    with pytest.raises(ValueError):
        dry_run_materialize(pkg, tmp_path)


def test_dry_run_refuses_overwrite(tmp_path):
    pkg = package()
    dry_run_materialize(pkg, tmp_path)
    with pytest.raises(FileExistsError):
        dry_run_materialize(pkg, tmp_path)


def test_ledger_rejects_negative_bool_bad_hash_and_status():
    pkg = package()
    bad = row(pkg)
    bad["input_tokens"] = -1
    bad["output_tokens"] = True
    bad["request_manifest_sha256"] = "not-a-hash"
    bad["status"] = "maybe"
    reasons = audit_ledger(pkg, [bad], summary(pkg), REQUIRED_ARTIFACTS)["reason_codes"]
    assert "ledger_numeric_invalid" in reasons
    assert "ledger_hash_invalid" not in reasons


def test_ledger_rejects_bad_hash_and_status_with_valid_numbers():
    pkg = package()
    bad = row(pkg)
    bad["request_manifest_sha256"] = "not-a-hash"
    bad["status"] = "maybe"
    reasons = audit_ledger(pkg, [bad], summary(pkg), REQUIRED_ARTIFACTS)["reason_codes"]
    assert "ledger_hash_invalid" in reasons
    assert "ledger_status_invalid" in reasons


def test_summary_extra_field_and_package_tamper_fail_closed():
    pkg = package()
    s = summary(pkg)
    s["extra"] = 1
    pkg["task_count"] += 1
    reasons = audit_ledger(pkg, [row(package())], s, REQUIRED_ARTIFACTS)["reason_codes"]
    assert "summary_schema_mismatch" in reasons
    assert "package_manifest_invalid" in reasons


def test_malformed_audit_input_fails_closed():
    pkg = package()
    result = audit_ledger(pkg, "bad", [], REQUIRED_ARTIFACTS)
    assert result["valid"] is False
    assert result["reason_codes"] == ["malformed_audit_input"]
