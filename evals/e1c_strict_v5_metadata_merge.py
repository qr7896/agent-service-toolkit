"""Merge safe partial metadata sources with field-level provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_metadata import audit_pool

OUT = ROOT / "data" / "e1c_strict_v5_merged_metadata_pool.json"
FIELDS = ("instance_id", "repo", "base_commit", "image")
CONTENT_KEYS = {
    "problem_statement",
    "statement",
    "test_patch",
    "gold_patch",
    "FAIL_TO_PASS",
    "PASS_TO_PASS",
    "grader",
    "resolved",
    "patch",
    "tests",
    "test",
}


def _rows(payload: object) -> list[dict]:
    if isinstance(payload, dict):
        rows = payload.get("tasks")
    else:
        rows = payload
    if not isinstance(rows, list):
        raise ValueError("partial metadata source must contain tasks list")
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("partial metadata rows must be objects")
    return rows


def _source(payload: dict[str, Any], path: Path) -> dict[str, Any]:
    revision = payload.get("source_revision")
    source_name = payload.get("source_name") or path.name
    if not isinstance(revision, str) or not revision:
        raise ValueError("partial metadata source_revision required")
    return {
        "source_name": str(source_name),
        "source_revision": revision,
        "source_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def merge(paths: list[Path]) -> dict:
    by_id: dict[str, dict[str, Any]] = defaultdict(dict)
    provenance: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    sources = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("partial metadata source must be an object")
        source = _source(payload, path)
        sources.append(source)
        for row in _rows(payload):
            if CONTENT_KEYS & set(row):
                raise ValueError("partial source contains forbidden task-content/outcome field")
            instance_id = row.get("instance_id")
            if not isinstance(instance_id, str) or not instance_id:
                raise ValueError("partial source row requires instance_id")
            for field in FIELDS:
                if field not in row:
                    continue
                value = row[field]
                if not isinstance(value, str) or not value:
                    raise ValueError(f"invalid partial metadata value: {field}")
                current = by_id[instance_id].get(field)
                if current is not None and current != value:
                    raise ValueError(f"conflicting metadata for {instance_id}:{field}")
                by_id[instance_id][field] = value
                provenance[instance_id][field] = {
                    **source,
                    "field": field,
                }

    complete = []
    incomplete = []
    for instance_id in sorted(by_id):
        row = by_id[instance_id]
        row.setdefault("instance_id", instance_id)
        missing = [field for field in FIELDS if field not in row]
        if missing:
            incomplete.append({"instance_id": instance_id, "missing_fields": missing})
            continue
        complete.append({field: row[field] for field in FIELDS})

    audit = audit_pool({"source_revision": "merged-partial-sources", "tasks": complete})
    value = {
        "schema": "e1c-strict-v5-merged-metadata-pool-v1",
        "source_revision": "merged-partial-sources",
        "provider_calls": 0,
        "task_content_inspected": False,
        "new_task_tree_touched": False,
        "sources": sources,
        "tasks": complete,
        "field_provenance": {
            instance_id: provenance[instance_id]
            for instance_id in sorted(provenance)
            if instance_id in {row["instance_id"] for row in complete}
        },
        "complete_count": len(complete),
        "eligible_count": audit["eligible_count"],
        "incomplete_count": len(incomplete),
        "incomplete": incomplete,
        "audit": {
            "eligible_sha256": audit["eligible_sha256"],
            "rejected": audit["rejected"],
        },
    }
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    value["merged_pool_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return value


def write(paths: list[Path], output: Path = OUT) -> dict:
    value = merge(paths)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(write(args.sources, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
