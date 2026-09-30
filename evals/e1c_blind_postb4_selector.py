"""Frozen post-B4 DEV selector. Selection metadata is evaluator-side, never repair evidence."""

from __future__ import annotations

import hashlib
import json

from evals.e1c_live_runner import MANIFEST_SHA256, _manifest

B4_IDS = frozenset({
    "sympy__sympy-13798",
    "pytest-dev__pytest-5631",
    "sympy__sympy-17318",
    "django__django-16100",
})
HISTORICAL_SOLVED_IDS = frozenset({
    "pytest-dev__pytest-5631",
    "django__django-11880",
    "django__django-15315",
    "matplotlib__matplotlib-24026",
    "astropy__astropy-8707",
    "django__django-16100",
    "django__django-13279",
    "scikit-learn__scikit-learn-11578",
    "django__django-11790",
    "django__django-11740",
    "django__django-13809",
    "django__django-13512",
    "django__django-15731",
})


def eligible_unresolved_rows() -> list[dict]:
    return [
        row
        for row in _manifest()["tasks"]
        if row["instance_id"] not in B4_IDS and row["instance_id"] not in HISTORICAL_SOLVED_IDS
    ]


def canary_rows(count: int = 6) -> list[dict]:
    eligible = eligible_unresolved_rows()
    repo_order: list[str] = []
    grouped: dict[str, list[dict]] = {}
    for row in eligible:
        repo = row["repo"]
        if repo not in grouped:
            repo_order.append(repo)
            grouped[repo] = []
        grouped[repo].append(row)
    selected: list[dict] = []
    depth = 0
    while len(selected) < min(count, len(eligible)):
        progressed = False
        for repo in repo_order:
            rows = grouped[repo]
            if depth < len(rows):
                selected.append(rows[depth])
                progressed = True
                if len(selected) == count:
                    break
        if not progressed:
            break
        depth += 1
    return selected


def frozen_selector_identity(count: int = 6) -> dict:
    rows = canary_rows(count)
    value = {
        "schema": "e1c-blind-postb4-selector-v1",
        "manifest_sha256": MANIFEST_SHA256,
        "historical_solved_ids": sorted(HISTORICAL_SOLVED_IDS),
        "b4_excluded_ids": sorted(B4_IDS),
        "rule": "eligible unresolved after B4 exclusion; round-robin by repo in first manifest appearance order",
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
