"""Acquire/freeze strict-v7 canary identity from official task.yaml metadata only."""

from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

from evals.e1c_admission import ROOT
from evals.e1c_strict_v6_official_metadata import SOURCE_REVISION, REQUIRED, _fetch_yaml, inventory
from evals.e1c_strict_v7_reserve import SALT, freeze
from evals.e1c_strict_v7_selection_boundary import denylist

POOL = ROOT / "data" / "e1c_strict_v7_official_metadata_pool.json"
MANIFEST = ROOT / "data" / "e1c_strict_v7_canary_manifest.json"


def ranked_candidates(rows: list[dict], *, limit: int = 24) -> list[dict]:
    touched = denylist()
    ranked = []
    for row in rows:
        instance_id = row["instance_id"]
        if instance_id in touched:
            continue
        rank = hashlib.sha256(f"{SALT}|{instance_id}".encode()).hexdigest()
        ranked.append((rank, row))
    ranked.sort(key=lambda item: (item[0], item[1]["instance_id"]))
    return [row for _, row in ranked[:limit]]


def acquire(*, candidate_limit: int = 24, output: Path = POOL) -> dict:
    candidates = ranked_candidates(inventory(), limit=candidate_limit)
    fetched = {}
    errors = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(_fetch_yaml, row["path"]): row for row in candidates}
        for future in as_completed(futures):
            candidate = futures[future]
            try:
                fetched[candidate["instance_id"]] = future.result()
            except Exception as exc:
                errors.append(
                    {"instance_id": candidate["instance_id"], "reason": f"{type(exc).__name__}: {exc}"}
                )
    tasks = []
    provenance = {}
    for candidate in candidates:
        raw = fetched.get(candidate["instance_id"])
        if raw is None:
            continue
        payload = yaml.safe_load(raw)
        if not isinstance(payload, dict):
            continue
        row = {key: payload.get(key) for key in REQUIRED}
        if row["instance_id"] != candidate["instance_id"]:
            continue
        if not all(isinstance(row[key], str) and row[key] for key in REQUIRED):
            continue
        if len(row["base_commit"]) != 40:
            continue
        tasks.append(row)
        provenance[row["instance_id"]] = {
            "task_yaml_path": candidate["path"],
            "task_yaml_sha256": hashlib.sha256(raw).hexdigest(),
            "inventory_source": candidate.get("inventory_source"),
            "inventory_revision": candidate.get("inventory_revision"),
        }
        if len(tasks) >= 12:
            break
    value = {
        "schema": "e1c-strict-v7-official-metadata-pool-v1",
        "source_revision": SOURCE_REVISION,
        "selection_salt": SALT,
        "provider_calls": 0,
        "task_content_inspected": False,
        "forbidden_task_files_read": [],
        "candidate_limit": candidate_limit,
        "tasks": tasks,
        "field_provenance": provenance,
        "fetch_errors": errors,
    }
    value["pool_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


def acquire_and_freeze(*, candidate_limit: int = 24) -> dict:
    pool = acquire(candidate_limit=candidate_limit)
    result = freeze(pool["tasks"], source_revision=SOURCE_REVISION, output=MANIFEST)
    return {
        "schema": "e1c-strict-v7-official-freeze-v1",
        "provider_calls": 0,
        "task_content_inspected": False,
        "forbidden_task_files_read": [],
        "pool_sha256": pool["pool_sha256"],
        "available_metadata_rows": len(pool["tasks"]),
        "fetch_error_count": len(pool["fetch_errors"]),
        "freeze": result,
    }


if __name__ == "__main__":
    print(json.dumps(acquire_and_freeze(), ensure_ascii=False, indent=2))
