"""Fail-closed selector for an external, disjoint reproducer-v4 canary reserve."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT

RESERVE_MANIFEST = ROOT / "data" / "e1c_blind_reproducer_v4_canary_manifest.json"
CANARY_COUNT = 3

CONTAMINATED_IDS = frozenset({
    "astropy__astropy-13453",
    "astropy__astropy-7671",
    "astropy__astropy-8707",
    "django__django-11740",
    "django__django-11790",
    "django__django-11880",
    "django__django-11964",
    "django__django-12754",
    "django__django-12774",
    "django__django-13279",
    "django__django-13512",
    "django__django-13809",
    "django__django-14373",
    "django__django-14787",
    "django__django-15280",
    "django__django-15315",
    "django__django-15563",
    "django__django-15695",
    "django__django-15731",
    "django__django-15957",
    "django__django-16100",
    "django__django-16454",
    "django__django-16502",
    "matplotlib__matplotlib-24026",
    "matplotlib__matplotlib-24570",
    "pylint-dev__pylint-7080",
    "pytest-dev__pytest-5631",
    "scikit-learn__scikit-learn-11578",
    "scikit-learn__scikit-learn-25747",
    "sphinx-doc__sphinx-8056",
    "sphinx-doc__sphinx-9230",
    "sphinx-doc__sphinx-9673",
    "sphinx-doc__sphinx-9711",
    "sympy__sympy-13031",
    "sympy__sympy-13798",
    "sympy__sympy-13877",
    "sympy__sympy-14711",
    "sympy__sympy-15875",
    "sympy__sympy-16792",
    "sympy__sympy-17318",
    "sympy__sympy-18211",
    "astropy__astropy-14539",
    "pytest-dev__pytest-7373",
    "sympy__sympy-20590",
})
FORBIDDEN_TASK_KEYS = frozenset({
    "problem_statement",
    "statement",
    "gold_patch",
    "test_patch",
    "FAIL_TO_PASS",
    "PASS_TO_PASS",
    "resolved",
    "grader",
    "expected_patch",
})


def reserve_status(path: Path = RESERVE_MANIFEST) -> dict:
    if not path.is_file():
        return {
            "schema": "e1c-blind-reproducer-v4-reserve-status-v1",
            "ready": False,
            "reason": "external_disjoint_canary_manifest_missing",
            "manifest_path": path.as_posix(),
            "new_task_tree_touched": False,
        }
    manifest = json.loads(path.read_text(encoding="utf-8"))
    tasks = manifest.get("tasks", [])
    ids = [row.get("instance_id") for row in tasks if isinstance(row, dict)]
    overlap = sorted(set(ids) & CONTAMINATED_IDS)
    forbidden = sorted({
        key
        for row in tasks
        if isinstance(row, dict)
        for key in row
        if key in FORBIDDEN_TASK_KEYS
    })
    required = {"instance_id", "repo", "base_commit", "image"}
    metadata_complete = all(
        isinstance(row, dict)
        and required <= set(row)
        and isinstance(row.get("instance_id"), str)
        and isinstance(row.get("repo"), str)
        and isinstance(row.get("base_commit"), str)
        and len(row["base_commit"]) == 40
        and isinstance(row.get("image"), str)
        for row in tasks
    )
    identity_frozen = manifest.get("identity_frozen_before_statement_materialization") is True
    source_ok = manifest.get("source") == "external_disjoint_canary_reserve"
    unique = len(ids) == len(set(ids))
    ready = (
        len(tasks) == CANARY_COUNT
        and metadata_complete
        and unique
        and not overlap
        and not forbidden
        and identity_frozen
        and source_ok
    )
    return {
        "schema": "e1c-blind-reproducer-v4-reserve-status-v1",
        "ready": ready,
        "reason": "ready" if ready else "reserve_identity_invalid",
        "manifest_path": path.as_posix(),
        "task_count": len(tasks),
        "overlap_with_contaminated": overlap,
        "forbidden_metadata_keys": forbidden,
        "identity_frozen_before_statement_materialization": identity_frozen,
        "source_ok": source_ok,
        "new_task_tree_touched": False,
    }


def canary_rows(count: int = CANARY_COUNT) -> list[dict]:
    status = reserve_status()
    if not status["ready"]:
        raise RuntimeError(f"reproducer-v4 reserve is not admitted: {status}")
    manifest = json.loads(RESERVE_MANIFEST.read_text(encoding="utf-8"))
    rows = manifest["tasks"]
    if count != CANARY_COUNT or len(rows) != CANARY_COUNT:
        raise ValueError("reproducer-v4 canary identity is exactly three tasks")
    return rows


def frozen_selector_identity(count: int = CANARY_COUNT) -> dict:
    rows = canary_rows(count)
    value = {
        "schema": "e1c-blind-reproducer-v4-selector-v1",
        "rule": (
            "exactly three metadata-only tasks from an external disjoint reserve; "
            "identity frozen before statement/source materialization"
        ),
        "contaminated_id_count": len(CONTAMINATED_IDS),
        "statement_content_inspected_before_freeze": False,
        "fresh30_task_tree_used": False,
        "tasks": [
            {
                "instance_id": row["instance_id"],
                "repo": row["repo"],
                "base_commit": row["base_commit"],
                "image": row["image"],
            }
            for row in rows
        ],
    }
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return {**value, "selector_sha256": hashlib.sha256(encoded.encode()).hexdigest()}
