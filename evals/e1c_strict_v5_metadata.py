"""Fail-closed metadata-only acquisition and contamination audit for strict-v5."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_reserve import OUT, freeze
from evals.e1c_strict_v5_selector import (
    FORBIDDEN_KEYS,
    PRIOR_CONTAMINATED_IDS,
    REQUIRED_KEYS,
)

CACHE = ROOT / ".codex" / "e1c" / "metadata-cache"
KNOWN_METADATA_MANIFESTS = (
    ROOT / "data" / "e1c_candidate_manifest.json",
    ROOT / ".codex" / "e1c" / "candidate_manifest.json",
    ROOT / ".codex" / "e1c" / "final_admitted_manifest.json",
)


def locally_touched_ids() -> frozenset[str]:
    ids = set(PRIOR_CONTAMINATED_IDS)
    if CACHE.is_dir():
        for path in CACHE.iterdir():
            name = path.name
            if name.endswith(".tests.json"):
                ids.add(name[: -len(".tests.json")])
            elif name.endswith(".yaml"):
                ids.add(name[:-5])
    for path in KNOWN_METADATA_MANIFESTS:
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows = payload.get("tasks", []) if isinstance(payload, dict) else []
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get("instance_id"), str):
                ids.add(row["instance_id"])
    return frozenset(ids)


def audit_pool(payload: object) -> dict:
    if isinstance(payload, dict):
        rows = payload.get("tasks")
        source_revision = payload.get("source_revision")
    else:
        rows = payload
        source_revision = None
    if not isinstance(rows, list):
        raise ValueError("metadata pool must be a list or object with tasks list")
    touched = locally_touched_ids()
    clean: list[dict] = []
    rejected: list[dict] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        reason = None
        if not isinstance(row, dict):
            reason = "not_object"
        elif FORBIDDEN_KEYS & set(row):
            reason = "forbidden_task_content_field"
        elif set(row) != REQUIRED_KEYS:
            reason = "metadata_keys_not_exact"
        elif not all(isinstance(row.get(key), str) and row[key] for key in REQUIRED_KEYS):
            reason = "metadata_value_invalid"
        elif len(row["base_commit"]) != 40:
            reason = "base_commit_invalid"
        elif row["instance_id"] in touched:
            reason = "identity_locally_touched_or_prior_lineage"
        elif row["instance_id"] in seen:
            reason = "duplicate_identity"
        if reason:
            rejected.append({
                "index": index,
                "instance_id": row.get("instance_id") if isinstance(row, dict) else None,
                "reason": reason,
            })
            continue
        seen.add(row["instance_id"])
        clean.append({key: row[key] for key in ("instance_id", "repo", "base_commit", "image")})
    canonical = json.dumps(clean, sort_keys=True, separators=(",", ":"))
    return {
        "schema": "e1c-strict-v5-metadata-pool-audit-v1",
        "source_revision": source_revision,
        "input_count": len(rows),
        "eligible_count": len(clean),
        "rejected_count": len(rejected),
        "locally_touched_identity_count": len(touched),
        "eligible": clean,
        "rejected": rejected,
        "eligible_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "provider_calls": 0,
        "task_content_inspected": False,
        "new_task_tree_touched": False,
    }


def audit_file(path: Path) -> dict:
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    result = audit_pool(payload)
    return {
        **result,
        "source_path": path.as_posix(),
        "source_file_sha256": hashlib.sha256(raw).hexdigest(),
    }


def freeze_file(path: Path, *, source_revision: str | None = None, output: Path = OUT) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    audit = audit_pool(payload)
    revision = source_revision or (
        payload.get("source_revision") if isinstance(payload, dict) else None
    )
    if not isinstance(revision, str) or not revision.strip():
        raise ValueError("immutable source_revision is required")
    if audit["eligible_count"] < 3:
        raise ValueError(
            f"need at least 3 untouched metadata-only candidates, got {audit['eligible_count']}"
        )
    result = freeze(audit["eligible"], source_revision=revision, output=output)
    return {
        **result,
        "source_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "metadata_audit_sha256": audit["eligible_sha256"],
        "locally_touched_identity_count": audit["locally_touched_identity_count"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("audit", "freeze"))
    parser.add_argument("metadata_json", type=Path)
    parser.add_argument("--source-revision")
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    result = (
        audit_file(args.metadata_json)
        if args.command == "audit"
        else freeze_file(
            args.metadata_json,
            source_revision=args.source_revision,
            output=args.output,
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
