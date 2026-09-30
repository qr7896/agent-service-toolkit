"""Strict-v8 candidate plan combining runtime and source-behavior witnesses."""

from __future__ import annotations

import hashlib
import json

from evals.e1c_strict_v7_probe import typed_candidates as v7_typed_candidates
from evals.e1c_strict_v8_source_contract import extract_source_contracts


def candidate_plan(projected_issue: str, localization: dict, *, limit: int = 10) -> dict:
    rows = list(v7_typed_candidates(projected_issue, localization, limit=limit))
    rows.extend(extract_source_contracts(projected_issue, localization))
    deduped = []
    seen = set()
    for row in rows:
        witness = row.get("witness") or row.get("freeze", {}).get("witness") or {}
        key = witness.get("witness_sha256") or row.get("row_sha256")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
        if len(deduped) >= limit:
            break
    executable = sum(bool(row.get("execution_ready")) for row in deduped)
    value = {
        "schema": "e1c-strict-v8-candidate-plan-v1",
        "candidate_count": len(deduped),
        "executable_candidate_count": executable,
        "status": "candidate_executable_witnesses" if executable else "no_executable_reproducer",
        "candidates": deduped,
        "provider_calls": 0,
        "benchmark_assertion_used": False,
    }
    value["plan_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value
