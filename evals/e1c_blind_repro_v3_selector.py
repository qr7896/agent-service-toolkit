"""Final unseen DEV selector for the frozen reproducer-v3 canary."""

from __future__ import annotations

import hashlib
import json

from evals.e1c_blind_postb4_selector import B4_IDS, HISTORICAL_SOLVED_IDS
from evals.e1c_blind_postb4_selector import canary_rows as c4_rows
from evals.e1c_blind_repro_selector import canary_rows as reproducer_v2_dev_rows
from evals.e1c_live_runner import MANIFEST_SHA256, _manifest

C4_IDS = frozenset(row["instance_id"] for row in c4_rows())
REPRODUCER_V2_DEV_IDS = frozenset(row["instance_id"] for row in reproducer_v2_dev_rows())
EXCLUDED_IDS = frozenset(B4_IDS | HISTORICAL_SOLVED_IDS | C4_IDS | REPRODUCER_V2_DEV_IDS)


def eligible_final_rows() -> list[dict]:
    return [
        row
        for row in _manifest()["tasks"]
        if row["instance_id"] not in EXCLUDED_IDS
    ]


def canary_rows(count: int = 3) -> list[dict]:
    eligible = eligible_final_rows()
    if len(eligible) < count:
        raise ValueError("not enough unseen unresolved DEV rows for reproducer-v3 canary")
    return eligible[:count]


def frozen_selector_identity(count: int = 3) -> dict:
    rows = canary_rows(count)
    value = {
        "schema": "e1c-blind-reproducer-v3-selector-v1",
        "manifest_sha256": MANIFEST_SHA256,
        "excluded_ids": sorted(EXCLUDED_IDS),
        "rule": "freeze the remaining unseen unresolved DEV rows in final manifest order after excluding historical solved, B4, C4, and reproducer-v2 development rows",
        "statement_content_inspected_before_freeze": False,
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
