"""Freeze a strict-v5 metadata-only independent-canary reserve."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_selector import (
    CANARY_COUNT,
    FORBIDDEN_KEYS,
    PRIOR_CONTAMINATED_IDS,
    REQUIRED_KEYS,
)

OUT = ROOT / "data" / "e1c_strict_v5_canary_manifest.json"


def freeze(rows: list[dict], *, source_revision: str, output: Path = OUT) -> dict:
    if not source_revision.strip():
        raise ValueError("source_revision is required")
    ranked: list[tuple[str, dict]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if FORBIDDEN_KEYS & set(row):
            raise ValueError("metadata input contains forbidden task-content/outcome fields")
        if not REQUIRED_KEYS <= set(row):
            continue
        identity = {key: row.get(key) for key in ("instance_id", "repo", "base_commit", "image")}
        if not all(isinstance(value, str) and value for value in identity.values()):
            continue
        if len(identity["base_commit"]) != 40:
            continue
        if identity["instance_id"] in PRIOR_CONTAMINATED_IDS:
            continue
        rank = hashlib.sha256(
            f"e1c-strict-v5-independent-canary|{identity['instance_id']}".encode()
        ).hexdigest()
        ranked.append((rank, identity))

    ranked.sort(key=lambda item: (item[0], item[1]["instance_id"]))
    selected: list[dict] = []
    seen: set[str] = set()
    for _, identity in ranked:
        if identity["instance_id"] in seen:
            continue
        seen.add(identity["instance_id"])
        selected.append(identity)
        if len(selected) == CANARY_COUNT:
            break
    if len(selected) != CANARY_COUNT:
        raise ValueError(
            f"need {CANARY_COUNT} disjoint metadata-complete candidates, got {len(selected)}"
        )

    manifest = {
        "schema": "e1c-strict-v5-external-canary-reserve-v1",
        "source": "external_disjoint_canary_reserve",
        "source_revision": source_revision,
        "selection_rule": (
            "lowest sha256(e1c-strict-v5-independent-canary|instance_id) after "
            "strict metadata validation and prior-lineage contamination exclusion"
        ),
        "identity_frozen_before_statement_materialization": True,
        "tasks": selected,
    }
    encoded = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(encoded, encoding="utf-8")
    return {
        "schema": "e1c-strict-v5-reserve-freeze-v1",
        "provider_calls": 0,
        "task_count": CANARY_COUNT,
        "instance_ids": [row["instance_id"] for row in selected],
        "source_revision": source_revision,
        "manifest_path": output.as_posix(),
        "manifest_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
        "statement_content_inspected_before_freeze": False,
        "new_task_tree_touched": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("metadata_json", type=Path)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    payload = json.loads(args.metadata_json.read_text(encoding="utf-8"))
    rows = payload.get("tasks") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("metadata_json must be a list or object with tasks list")
    print(json.dumps(
        freeze(rows, source_revision=args.source_revision, output=args.output),
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
