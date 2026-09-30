"""Fresh non-overlapping DEV selector for the reproducer-focused canary."""

from __future__ import annotations

import hashlib
import json

from evals.e1c_blind_postb4_selector import (
    B4_IDS,
    HISTORICAL_SOLVED_IDS,
)
from evals.e1c_blind_postb4_selector import (
    canary_rows as c4_rows,
)
from evals.e1c_live_runner import MANIFEST_SHA256, _manifest

C4_IDS = frozenset(row["instance_id"] for row in c4_rows())
EXCLUDED_IDS = frozenset(B4_IDS | HISTORICAL_SOLVED_IDS | C4_IDS)


def eligible_reproducer_rows() -> list[dict]:
    return [
        row
        for row in _manifest()["tasks"]
        if row["instance_id"] not in EXCLUDED_IDS
    ]


def canary_rows(count: int = 6) -> list[dict]:
    eligible = eligible_reproducer_rows()
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
        "schema": "e1c-blind-reproducer-selector-v1",
        "manifest_sha256": MANIFEST_SHA256,
        "excluded_ids": sorted(EXCLUDED_IDS),
        "rule": "exclude historical solved, B4 and C4; round-robin remaining unresolved by repo in manifest order",
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
