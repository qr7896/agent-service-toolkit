"""Strict-v6 repair-visible runtime using the frozen strict-v5 boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_blind_evidence import extract_contract
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload, project_issue
from evals.e1c_strict_v5_runtime import localize
from evals.e1c_strict_v6_probe import freeze_witness_plan


def build_bundle(
    *,
    statement: str,
    workspace: Path,
    base_commit: str,
    forbidden_values: tuple[str, ...] = (),
    limit: int = 6,
) -> dict:
    projection = project_issue(statement)
    localization = localize(projection.text, workspace, limit=limit)
    witness_plan = freeze_witness_plan(projection.text, localization)
    value = {
        "schema": "e1c-strict-v6-agent-bundle-v1",
        "issue": projection.text,
        "issue_projection_sha256": projection.sha256,
        "source_commit": base_commit,
        "contract": extract_contract(projection.text),
        "localization": localization,
        "witness_plan": witness_plan,
        "candidate_paths": localization["candidate_paths"],
        "inspect_budget": {"max_calls": 1, "max_chars": 4000, "max_unique_paths": 1},
    }
    value["bundle_sha256"] = audit_repair_visible_payload(
        value,
        forbidden_values=forbidden_values,
    )
    return value


def mechanism_identity(paths: tuple[Path, ...]) -> dict:
    files = []
    for path in paths:
        raw = path.read_bytes()
        files.append({
            "path": path.as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    value = {
        "schema": "e1c-strict-v6-mechanism-identity-v1",
        "files": files,
    }
    value["mechanism_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value
