"""Metadata-only, reproducible selection of a supplementary E1-C DEV cohort."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POOL = ROOT / "data/e1c_strict_v20_clean_metadata_pool.json"
SALT = "e1c-reproducer-development-2026-09-27"


def _hash(value: str) -> str:
    return hashlib.sha256((SALT + "\0" + value).encode()).hexdigest()


def _identities(value: object) -> set[str]:
    if isinstance(value, dict):
        result = {value["instance_id"]} if isinstance(value.get("instance_id"), str) else set()
        for child in value.values():
            result.update(_identities(child))
        return result
    if isinstance(value, list):
        result: set[str] = set()
        for child in value:
            result.update(_identities(child))
        return result
    return set()


def build() -> dict:
    pool_bytes = POOL.read_bytes()
    pool = json.loads(pool_bytes)
    assert pool["tree_truncated"] is False and pool["task_content_inspected"] is False
    exclusion_paths = sorted(
        {ROOT / "data/e1c_candidate_manifest.json"}
        | set((ROOT / "data").glob("e1c_strict_v*_canary_manifest.json"))
        | set((ROOT / "data").glob("e1c_strict_successor*_canary_identity.json"))
    )
    excluded: set[str] = set()
    exclusions = []
    for path in exclusion_paths:
        payload = path.read_bytes()
        excluded.update(_identities(json.loads(payload)))
        exclusions.append({"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(payload).hexdigest()})
    by_repo: dict[str, list[dict]] = {}
    for row in pool["tasks"]:
        iid = row["instance_id"]
        if iid not in excluded:
            by_repo.setdefault(iid.split("__", 1)[0], []).append(row)
    repos = sorted(by_repo, key=_hash)[:4]
    tasks = [row for repo in repos for row in sorted(by_repo[repo], key=lambda x: _hash(x["instance_id"]))[:3]]
    assert len(tasks) == 12 and len({row["instance_id"] for row in tasks}) == 12
    return {
        "schema": "e1c-reproducer-development-metadata-identity-v1",
        "role": "development_only_never_independent_canary_or_fresh30",
        "source_revision": pool["source_revision"],
        "pool_path": POOL.relative_to(ROOT).as_posix(),
        "pool_file_sha256": hashlib.sha256(pool_bytes).hexdigest(),
        "selection_rule": "four lowest salted-hash repo keys, then three lowest salted-hash instance IDs per repo",
        "salt": SALT,
        "exclusion_files": exclusions,
        "excluded_identity_count": len(excluded),
        "task_content_inspected_at_selection": False,
        "provider_calls": 0,
        "tasks": tasks,
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
