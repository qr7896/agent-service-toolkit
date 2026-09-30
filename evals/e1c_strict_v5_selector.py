"""Metadata-only selector for the strict-v5 independent three-task canary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_blind_repro_v4_selector import CONTAMINATED_IDS as PRIOR_CONTAMINATED_IDS

CANARY_COUNT = 3
RESERVE_MANIFEST = ROOT / "data" / "e1c_strict_v5_canary_manifest.json"
FORBIDDEN_KEYS = frozenset({
    "problem_statement",
    "statement",
    "gold_patch",
    "test_patch",
    "FAIL_TO_PASS",
    "PASS_TO_PASS",
    "resolved",
    "grader",
    "expected_patch",
    "patch",
    "tests",
    "test",
})
REQUIRED_KEYS = frozenset({"instance_id", "repo", "base_commit", "image"})


def reserve_status(path: Path = RESERVE_MANIFEST) -> dict:
    if not path.is_file():
        return {
            "schema": "e1c-strict-v5-reserve-status-v1",
            "ready": False,
            "reason": "external_disjoint_canary_manifest_missing",
            "provider_calls": 0,
            "new_task_tree_touched": False,
            "manifest_path": path.as_posix(),
        }
    manifest = json.loads(path.read_text(encoding="utf-8"))
    rows = manifest.get("tasks", [])
    ids = [row.get("instance_id") for row in rows if isinstance(row, dict)]
    overlap = sorted(set(ids) & PRIOR_CONTAMINATED_IDS)
    forbidden = sorted({
        key
        for row in rows
        if isinstance(row, dict)
        for key in row
        if key in FORBIDDEN_KEYS
    })
    complete = all(
        isinstance(row, dict)
        and REQUIRED_KEYS <= set(row)
        and set(row) <= REQUIRED_KEYS
        and all(isinstance(row.get(key), str) and row[key] for key in REQUIRED_KEYS)
        and len(row["base_commit"]) == 40
        for row in rows
    )
    ready = (
        manifest.get("schema") == "e1c-strict-v5-external-canary-reserve-v1"
        and manifest.get("source") == "external_disjoint_canary_reserve"
        and manifest.get("identity_frozen_before_statement_materialization") is True
        and isinstance(manifest.get("source_revision"), str)
        and bool(manifest.get("source_revision"))
        and len(rows) == CANARY_COUNT
        and len(ids) == len(set(ids))
        and complete
        and not overlap
        and not forbidden
    )
    return {
        "schema": "e1c-strict-v5-reserve-status-v1",
        "ready": ready,
        "reason": "ready" if ready else "reserve_identity_invalid",
        "provider_calls": 0,
        "new_task_tree_touched": False,
        "manifest_path": path.as_posix(),
        "task_count": len(rows),
        "overlap_with_prior_contaminated": overlap,
        "forbidden_keys": forbidden,
        "identity_frozen_before_statement_materialization": (
            manifest.get("identity_frozen_before_statement_materialization") is True
        ),
    }


def canary_rows(path: Path = RESERVE_MANIFEST) -> list[dict]:
    status = reserve_status(path)
    if not status["ready"]:
        raise RuntimeError(f"strict-v5 reserve is not admitted: {status}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    return list(manifest["tasks"])


def frozen_selector_identity(path: Path = RESERVE_MANIFEST) -> dict:
    rows = canary_rows(path)
    value = {
        "schema": "e1c-strict-v5-selector-v1",
        "rule": (
            "exactly three external metadata-only identities, deterministically frozen "
            "before any statement/test/gold/grader materialization"
        ),
        "statement_content_inspected_before_freeze": False,
        "fresh30_task_tree_used": False,
        "tasks": rows,
    }
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {**value, "selector_sha256": hashlib.sha256(encoded.encode()).hexdigest()}
