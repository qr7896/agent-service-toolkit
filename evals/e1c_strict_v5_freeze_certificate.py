"""Verify a frozen strict-v5 metadata identity before task materialization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_selector import FORBIDDEN_KEYS, REQUIRED_KEYS

MANIFEST = ROOT / "data" / "e1c_strict_v5_canary_manifest.json"
AUDIT = ROOT / "data" / "e1c_strict_v5_metadata_audit.json"
OUT = ROOT / "data" / "e1c_strict_v5_freeze_certificate.json"


def certify(
    manifest_path: Path = MANIFEST,
    audit_path: Path = AUDIT,
    output: Path | None = OUT,
) -> dict:
    if not manifest_path.is_file() or not audit_path.is_file():
        return {
            "schema": "e1c-strict-v5-freeze-certificate-v1",
            "ready": False,
            "reason": "manifest_or_metadata_audit_missing",
            "provider_calls": 0,
            "task_content_inspected": False,
            "new_task_tree_touched": False,
        }
    manifest_bytes = manifest_path.read_bytes()
    audit_bytes = audit_path.read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    audit = json.loads(audit_bytes.decode("utf-8"))
    rows = manifest.get("tasks", [])
    eligible_rows = audit.get("eligible", []) if isinstance(audit.get("eligible"), list) else []
    eligible_by_id = {
        row.get("instance_id"): row
        for row in eligible_rows
        if isinstance(row, dict) and isinstance(row.get("instance_id"), str)
    }
    checks = {
        "exact_task_count": isinstance(rows, list) and len(rows) == 3,
        "source_revision_present": isinstance(manifest.get("source_revision"), str)
        and bool(manifest.get("source_revision")),
        "identity_frozen_before_statement": manifest.get(
            "identity_frozen_before_statement_materialization"
        )
        is True,
        "audit_provider_calls_zero": audit.get("provider_calls") == 0,
        "audit_task_content_inspected_false": audit.get("task_content_inspected") is False,
        "audit_source_revision_matches": audit.get("source_revision") == manifest.get("source_revision"),
    }
    ids = []
    exact_schema = True
    valid_values = True
    no_forbidden = True
    audit_membership_mismatch = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            exact_schema = False
            valid_values = False
            continue
        exact_schema &= set(row) == REQUIRED_KEYS
        no_forbidden &= not bool(FORBIDDEN_KEYS & set(row))
        valid_values &= all(isinstance(row.get(key), str) and row[key] for key in REQUIRED_KEYS)
        valid_values &= isinstance(row.get("base_commit"), str) and len(row["base_commit"]) == 40
        if isinstance(row.get("instance_id"), str):
            ids.append(row["instance_id"])
            audited = eligible_by_id.get(row["instance_id"])
            if audited != row:
                audit_membership_mismatch.append(row["instance_id"])
    checks.update({
        "exact_metadata_schema": exact_schema,
        "no_forbidden_content_fields": no_forbidden,
        "valid_required_values": valid_values,
        "unique_identities": len(ids) == len(set(ids)) == 3,
        "freeze_rows_match_audit_snapshot": not audit_membership_mismatch,
    })
    ready = all(checks.values())
    value = {
        "schema": "e1c-strict-v5-freeze-certificate-v1",
        "ready": ready,
        "reason": "identity_freeze_certified" if ready else "identity_freeze_integrity_failed",
        "provider_calls": 0,
        "task_content_inspected": False,
        "new_task_tree_touched": False,
        "checks": checks,
        "audit_membership_mismatch": sorted(audit_membership_mismatch),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "metadata_audit_sha256": hashlib.sha256(audit_bytes).hexdigest(),
        "source_revision": manifest.get("source_revision"),
        "instance_ids": ids,
    }
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


if __name__ == "__main__":
    print(json.dumps(certify(), ensure_ascii=False, indent=2))
