import hashlib
import json
import re
from dataclasses import dataclass

from evals.e1b_acquisition_policy_interface_v10_4 import audit_feature_leakage
from evals.e1b_freeze_manifest_v10_6 import EXCLUDED_SOURCES, content_manifest, verify_manifest

SCHEMA_VERSION = "e1b-experiment-admission-v1"
ALLOWED_TASK_METADATA = {
    "task_count", "repo_ids", "commit_ids", "curation_timestamps",
    "overlap_audit_passed", "source_commit_overlap", "manifest_sha256",
    "base_fail_attested", "gold_pass_independently_attested",
}
FORBIDDEN_TOKENS = (
    "task_text", "issue_text", "setup", "hidden_test", "gold_source", "gold_patch",
    "expected_value", "expected_patch", "symbol", "grader", "outcome",
)
SECRET_TOKENS = ("api_key", "token", "password", "secret", "credential")
FROZEN_ID_FIELDS = (
    "model_id", "editor_prompt_sha256", "runtime_sha256", "retrieval_policy_sha256",
    "tool_config_sha256", "sandbox_config_sha256", "analysis_script_sha256",
    "experiment_arm_id",
)


@dataclass(frozen=True)
class AdmissionConfig:
    task_metadata: dict
    data_isolation: tuple[str, ...]
    frozen_identifiers: dict
    provider_call_ceiling: int
    provider_token_ceiling: int
    one_shot_frozen: bool
    runtime_features: tuple[dict, ...] = ()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def _looks_frozen(value):
    if not isinstance(value, str) or not value.strip():
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9._:/@+-]{3,200}", value))


def _secret_like(mapping):
    return sorted(
        key for key in mapping
        if any(token in str(key).lower() for token in SECRET_TOKENS)
    )


def admit(config, freeze_manifest=None):
    reasons = []
    frozen = freeze_manifest or content_manifest()
    freeze_check = verify_manifest(frozen)
    if not freeze_check["valid"]:
        reasons.append("freeze_manifest_invalid")

    metadata = config.task_metadata
    unknown = sorted(set(metadata) - ALLOWED_TASK_METADATA)
    forbidden = sorted(
        key for key in metadata
        if any(token in str(key).lower() for token in FORBIDDEN_TOKENS)
    )
    if unknown or forbidden:
        reasons.append("forbidden_task_metadata")
    required = {
        "task_count", "repo_ids", "commit_ids", "curation_timestamps",
        "overlap_audit_passed", "source_commit_overlap", "manifest_sha256",
        "base_fail_attested", "gold_pass_independently_attested",
    }
    if not required.issubset(metadata):
        reasons.append("task_metadata_incomplete")
    elif (
        not isinstance(metadata["task_count"], int)
        or isinstance(metadata["task_count"], bool)
        or metadata["task_count"] <= 0
        or not metadata["repo_ids"]
        or not metadata["commit_ids"]
        or not metadata["curation_timestamps"]
        or not _looks_frozen(metadata["manifest_sha256"])
    ):
        reasons.append("task_metadata_invalid")
    if metadata.get("overlap_audit_passed") is not True or metadata.get("source_commit_overlap") not in (False, [], (), None):
        reasons.append("overlap_audit_failed")
    if metadata.get("base_fail_attested") is not True or metadata.get("gold_pass_independently_attested") is not True:
        reasons.append("heldout_attestation_missing")

    if tuple(config.data_isolation) != tuple(EXCLUDED_SOURCES):
        reasons.append("data_isolation_mismatch")

    identifiers = config.frozen_identifiers
    if _secret_like(identifiers):
        reasons.append("secret_like_identifier_field")
    if set(FROZEN_ID_FIELDS) - set(identifiers):
        reasons.append("frozen_identifiers_incomplete")
    elif any(not _looks_frozen(identifiers[field]) for field in FROZEN_ID_FIELDS):
        reasons.append("frozen_identifier_invalid")

    if (
        not isinstance(config.provider_call_ceiling, int)
        or isinstance(config.provider_call_ceiling, bool)
        or config.provider_call_ceiling <= 0
        or not isinstance(config.provider_token_ceiling, int)
        or isinstance(config.provider_token_ceiling, bool)
        or config.provider_token_ceiling <= 0
    ):
        reasons.append("provider_budget_invalid")
    if config.one_shot_frozen is not True:
        reasons.append("config_not_one_shot_frozen")
    try:
        audit_feature_leakage(config.runtime_features)
    except ValueError:
        reasons.append("runtime_feature_leakage")

    unique = sorted(set(reasons))
    result = {
        "schema_version": SCHEMA_VERSION,
        "decision": "ADMIT_OFFLINE_READY" if not unique else "REJECT",
        "reason_codes": unique or ["all_admission_checks_passed"],
        "starts_experiment": False,
        "freeze_manifest_sha256": frozen.get("content_manifest_sha256"),
        "task_manifest_sha256": metadata.get("manifest_sha256"),
        "claim_boundary": "admission readiness only; this gate never starts or authorizes a live experiment",
    }
    result["admission_manifest_sha256"] = sha256(result)
    return result
