import hashlib
import json
from pathlib import Path

SCHEMA_VERSION = "e1b-experiment-package-v1"
LEDGER_SCHEMA_VERSION = "e1b-provider-ledger-v1"
REQUIRED_ARTIFACTS = (
    "experiment_package.json",
    "provider_calls.jsonl",
    "task_outcomes.jsonl",
    "run_summary.json",
    "artifact_audit.json",
)
LEDGER_FIELDS = (
    "schema_version", "sequence", "run_id", "call_index", "model_id",
    "request_manifest_sha256", "response_manifest_sha256",
    "input_tokens", "output_tokens", "total_tokens", "status",
)
FORBIDDEN_METADATA_TOKENS = (
    "api_key", "password", "secret", "credential", "access_token", "auth_token",
    "prompt_text", "response_text", "task_text", "issue_text", "hidden_test",
    "gold_patch", "expected_patch", "grader_data", "outcome_text",
)
VALID_LEDGER_STATUSES = {"completed", "failed"}
SUMMARY_FIELDS = {
    "run_id", "provider_calls", "total_tokens", "task_outcome_count",
    "forbidden_source_accesses", "package_manifest_sha256",
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def audit_metadata(value):
    violations = []

    def walk(item, path="root"):
        if isinstance(item, dict):
            for key, nested in item.items():
                lowered = str(key).lower()
                if any(token in lowered for token in FORBIDDEN_METADATA_TOKENS):
                    violations.append(f"{path}.{key}")
                walk(nested, f"{path}.{key}")
        elif isinstance(item, (list, tuple)):
            for index, nested in enumerate(item):
                walk(nested, f"{path}[{index}]")

    walk(value)
    if violations:
        raise ValueError(f"forbidden metadata fields: {sorted(set(violations))}")
    return {"metadata_leakage": []}


def build_package(admission, config):
    if admission.get("decision") != "ADMIT_OFFLINE_READY" or admission.get("starts_experiment") is not False:
        raise ValueError("admission_not_offline_ready")
    identifiers = dict(config.frozen_identifiers)
    package = {
        "schema_version": SCHEMA_VERSION,
        "freeze_manifest_sha256": admission["freeze_manifest_sha256"],
        "admission_manifest_sha256": admission["admission_manifest_sha256"],
        "task_manifest_sha256": admission["task_manifest_sha256"],
        "task_count": config.task_metadata["task_count"],
        "frozen_identifiers": identifiers,
        "provider_call_ceiling": config.provider_call_ceiling,
        "provider_token_ceiling": config.provider_token_ceiling,
        "one_shot_frozen": config.one_shot_frozen,
        "required_artifacts": list(REQUIRED_ARTIFACTS),
        "provider_ledger_schema": LEDGER_SCHEMA_VERSION,
        "starts_experiment": False,
        "claim_boundary": "immutable experiment metadata package only; no provider execution or efficacy claim",
    }
    audit_metadata(package)
    stable = dict(package)
    stable["run_id"] = "e1b-" + sha256(package)[:16]
    stable["package_manifest_sha256"] = sha256(stable)
    return stable


def verify_package(package):
    try:
        audit_metadata(package)
    except ValueError:
        return {"valid": False, "reason": "forbidden_metadata"}
    expected = dict(package)
    manifest = expected.pop("package_manifest_sha256", None)
    run_id = expected.pop("run_id", None)
    if run_id != "e1b-" + sha256(expected)[:16]:
        return {"valid": False, "reason": "run_id_drift"}
    expected["run_id"] = run_id
    if manifest != sha256(expected):
        return {"valid": False, "reason": "package_manifest_drift"}
    if package.get("required_artifacts") != list(REQUIRED_ARTIFACTS):
        return {"valid": False, "reason": "artifact_contract_drift"}
    if package.get("provider_ledger_schema") != LEDGER_SCHEMA_VERSION:
        return {"valid": False, "reason": "ledger_schema_drift"}
    return {"valid": True, "reason": "verified"}


def dry_run_materialize(package, directory):
    if not verify_package(package)["valid"]:
        raise ValueError("package_not_verified")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if any((directory / name).exists() for name in REQUIRED_ARTIFACTS):
        raise FileExistsError("refusing_to_overwrite_experiment_artifact")
    (directory / "experiment_package.json").write_text(
        json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (directory / "provider_calls.jsonl").write_text("", encoding="utf-8")
    (directory / "task_outcomes.jsonl").write_text("", encoding="utf-8")
    template = {
        "run_id": package["run_id"],
        "provider_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "task_outcome_count": 0,
        "forbidden_source_accesses": 0,
        "dry_run": True,
    }
    (directory / "run_summary.json").write_text(
        json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (directory / "artifact_audit.json").write_text(
        json.dumps({"status": "DRY_RUN_ONLY", "starts_experiment": False}, indent=2),
        encoding="utf-8",
    )
    return {
        "directory": str(directory),
        "created_artifacts": list(REQUIRED_ARTIFACTS),
        "provider_calls": 0,
        "starts_experiment": False,
    }


def audit_ledger(package, rows, summary, present_artifacts):
    reasons = []
    if not verify_package(package)["valid"]:
        reasons.append("package_manifest_invalid")
    if not isinstance(rows, (list, tuple)) or not isinstance(summary, dict):
        return {"valid": False, "reason_codes": ["malformed_audit_input"], "provider_calls": 0, "total_tokens": 0, "claim_boundary": "post-run artifact reconciliation only; no repair efficacy conclusion"}
    if set(summary) != SUMMARY_FIELDS:
        reasons.append("summary_schema_mismatch")
    try:
        audit_metadata(rows)
        audit_metadata(summary)
    except ValueError:
        reasons.append("forbidden_metadata")
    if set(REQUIRED_ARTIFACTS) - set(present_artifacts):
        reasons.append("missing_required_artifact")
    expected_model = package["frozen_identifiers"]["model_id"]
    total_tokens = 0
    for index, row in enumerate(rows):
        if set(row) != set(LEDGER_FIELDS):
            reasons.append("ledger_schema_mismatch")
            continue
        if row["schema_version"] != LEDGER_SCHEMA_VERSION:
            reasons.append("ledger_schema_mismatch")
        numeric = (row["sequence"], row["call_index"], row["input_tokens"], row["output_tokens"], row["total_tokens"])
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in numeric):
            reasons.append("ledger_numeric_invalid")
            continue
        if row["status"] not in VALID_LEDGER_STATUSES:
            reasons.append("ledger_status_invalid")
        for field in ("request_manifest_sha256", "response_manifest_sha256"):
            value = row[field]
            if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value.lower()):
                reasons.append("ledger_hash_invalid")
        if row["sequence"] != index + 1 or row["call_index"] != index:
            reasons.append("ledger_index_nonmonotonic")
        if row["run_id"] != package["run_id"]:
            reasons.append("ledger_run_id_mismatch")
        if row["model_id"] != expected_model:
            reasons.append("ledger_model_mismatch")
        if row["total_tokens"] != row["input_tokens"] + row["output_tokens"]:
            reasons.append("ledger_token_reconciliation_failed")
        total_tokens += row.get("total_tokens", 0)
    if len(rows) > package["provider_call_ceiling"] or total_tokens > package["provider_token_ceiling"]:
        reasons.append("provider_budget_exceeded")
    if summary.get("provider_calls") != len(rows) or summary.get("total_tokens") != total_tokens:
        reasons.append("summary_reconciliation_failed")
    if summary.get("run_id") != package["run_id"]:
        reasons.append("summary_run_id_mismatch")
    if summary.get("task_outcome_count") != package["task_count"]:
        reasons.append("task_outcome_count_mismatch")
    if summary.get("forbidden_source_accesses") != 0:
        reasons.append("forbidden_source_access")
    if summary.get("package_manifest_sha256") != package["package_manifest_sha256"]:
        reasons.append("manifest_chain_drift")
    return {
        "valid": not reasons,
        "reason_codes": sorted(set(reasons)) or ["audit_passed"],
        "provider_calls": len(rows),
        "total_tokens": total_tokens,
        "claim_boundary": "post-run artifact reconciliation only; no repair efficacy conclusion",
    }
