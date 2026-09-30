"""Freeze a metadata-only, disjoint reproducer-v4 canary reserve."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_blind_repro_v4_selector import CANARY_COUNT, CONTAMINATED_IDS, FORBIDDEN_TASK_KEYS

OUT = ROOT / "data" / "e1c_blind_reproducer_v4_canary_manifest.json"
REQUIRED = frozenset({"instance_id", "repo", "base_commit", "image"})


def freeze(rows: list[dict], *, source_revision: str, output: Path = OUT) -> dict:
    if not source_revision:
        raise ValueError("source_revision is required")
    candidates: list[tuple[str, dict]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if FORBIDDEN_TASK_KEYS & set(row):
            raise ValueError("metadata input contains forbidden task-content/outcome fields")
        if not REQUIRED <= set(row):
            continue
        instance_id = row.get("instance_id")
        if not isinstance(instance_id, str) or instance_id in CONTAMINATED_IDS:
            continue
        if not all(isinstance(row.get(key), str) and row[key] for key in REQUIRED):
            continue
        if len(row["base_commit"]) != 40:
            continue
        identity = {key: row[key] for key in ("instance_id", "repo", "base_commit", "image")}
        rank = hashlib.sha256(f"e1c-v4-independent-canary|{instance_id}".encode()).hexdigest()
        candidates.append((rank, identity))
    candidates.sort(key=lambda item: (item[0], item[1]["instance_id"]))
    unique: list[dict] = []
    seen: set[str] = set()
    for _, row in candidates:
        if row["instance_id"] in seen:
            continue
        seen.add(row["instance_id"])
        unique.append(row)
        if len(unique) == CANARY_COUNT:
            break
    if len(unique) != CANARY_COUNT:
        raise ValueError(f"need {CANARY_COUNT} disjoint metadata-complete candidates, got {len(unique)}")
    manifest = {
        "schema": "e1c-blind-reproducer-v4-external-canary-reserve-v1",
        "source": "external_disjoint_canary_reserve",
        "source_revision": source_revision,
        "selection_rule": "lowest sha256(e1c-v4-independent-canary|instance_id) after contamination and metadata validation",
        "identity_frozen_before_statement_materialization": True,
        "tasks": unique,
    }
    encoded = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(encoded, encoding="utf-8")
    return {
        "schema": "e1c-blind-reproducer-v4-reserve-freeze-v1",
        "provider_calls": 0,
        "task_count": len(unique),
        "instance_ids": [row["instance_id"] for row in unique],
        "source_revision": source_revision,
        "manifest_path": output.as_posix(),
        "manifest_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
        "statement_content_inspected_before_freeze": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("metadata_json", type=Path)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    payload = json.loads(args.metadata_json.read_text(encoding="utf-8"))
    rows = payload["tasks"] if isinstance(payload, dict) and isinstance(payload.get("tasks"), list) else payload
    if not isinstance(rows, list):
        raise ValueError("metadata_json must be a list or an object with a tasks list")
    print(json.dumps(freeze(rows, source_revision=args.source_revision, output=args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
