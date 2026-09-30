"""Normalize external metadata-only pools without opening task content."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_metadata import audit_pool
from evals.e1c_strict_v5_reserve import OUT, freeze

AUDIT_OUT = ROOT / "data" / "e1c_strict_v5_metadata_audit.json"


def load_rows(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            rows = payload.get("tasks")
        else:
            rows = payload
    elif suffix == ".jsonl":
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    elif suffix == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    else:
        raise ValueError("strict-v5 metadata source must be .json, .jsonl, or .csv")
    if not isinstance(rows, list):
        raise ValueError("metadata source must contain a row list")
    return rows


def audit_source(path: Path, *, source_revision: str) -> dict:
    if not source_revision.strip():
        raise ValueError("immutable source_revision is required")
    raw = path.read_bytes()
    rows = load_rows(path)
    result = audit_pool({"source_revision": source_revision, "tasks": rows})
    return {
        **result,
        "source_path": path.as_posix(),
        "source_format": path.suffix.lower().lstrip("."),
        "source_file_sha256": hashlib.sha256(raw).hexdigest(),
    }


def write_audit(path: Path, *, source_revision: str, output: Path = AUDIT_OUT) -> dict:
    result = audit_source(path, source_revision=source_revision)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def freeze_source(
    path: Path,
    *,
    source_revision: str,
    output: Path = OUT,
    audit_output: Path = AUDIT_OUT,
) -> dict:
    audit = write_audit(path, source_revision=source_revision, output=audit_output)
    if audit["eligible_count"] < 3:
        raise ValueError(
            f"need at least 3 untouched metadata-only candidates, got {audit['eligible_count']}"
        )
    result = freeze(audit["eligible"], source_revision=source_revision, output=output)
    return {
        **result,
        "source_file_sha256": audit["source_file_sha256"],
        "metadata_audit_sha256": hashlib.sha256(
            audit_output.read_bytes()
        ).hexdigest(),
        "eligible_pool_sha256": audit["eligible_sha256"],
        "metadata_audit_path": audit_output.as_posix(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("audit", "freeze"))
    parser.add_argument("source", type=Path)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--audit-output", type=Path, default=AUDIT_OUT)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    if args.command == "audit":
        result = write_audit(
            args.source,
            source_revision=args.source_revision,
            output=args.audit_output,
        )
    else:
        result = freeze_source(
            args.source,
            source_revision=args.source_revision,
            output=args.output,
            audit_output=args.audit_output,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
