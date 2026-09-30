"""Build a source-counted strict-v5 contamination ledger."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_metadata import CACHE, KNOWN_METADATA_MANIFESTS
from evals.e1c_strict_v5_selector import PRIOR_CONTAMINATED_IDS

OUT = ROOT / "data" / "e1c_strict_v5_contamination_ledger.json"


def build() -> dict:
    sources: dict[str, set[str]] = defaultdict(set)
    sources["prior_v4_contaminated"].update(PRIOR_CONTAMINATED_IDS)
    if CACHE.is_dir():
        for path in CACHE.iterdir():
            if path.name.endswith(".tests.json"):
                sources["metadata_cache_tests"].add(path.name[: -len(".tests.json")])
            elif path.name.endswith(".yaml"):
                sources["metadata_cache_yaml"].add(path.name[:-5])
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
        key = "manifest:" + path.relative_to(ROOT).as_posix()
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get("instance_id"), str):
                sources[key].add(row["instance_id"])
    all_ids = sorted(set().union(*sources.values()) if sources else set())
    value = {
        "schema": "e1c-strict-v5-contamination-ledger-v1",
        "provider_calls": 0,
        "task_content_inspected": False,
        "new_task_tree_touched": False,
        "unique_identity_count": len(all_ids),
        "source_counts": {key: len(value) for key, value in sorted(sources.items())},
        "identity_sha256": hashlib.sha256(
            json.dumps(all_ids, separators=(",", ":")).encode()
        ).hexdigest(),
        "identities": all_ids,
    }
    return value


def write(output: Path = OUT) -> dict:
    value = build()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


if __name__ == "__main__":
    print(json.dumps(write(), ensure_ascii=False, indent=2))
