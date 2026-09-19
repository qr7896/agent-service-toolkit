from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.v2_dataset import validate_records
from evals.v2_replay_gate import SourceProvenance, replay_eligibility


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_dataset_manifest(dataset: Path, sources: list[Path], *, min_records: int = 200, provenance: list[SourceProvenance] | None = None) -> dict:
    records = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    validation = validate_records(records, min_records=min_records)
    eligibility = replay_eligibility(validation, provenance or [])
    return {
        "protocol": "v2-dataset-manifest-v1",
        "dataset": dataset.as_posix(),
        "dataset_sha256": file_sha256(dataset),
        "sources": {source.as_posix(): file_sha256(source) for source in sources},
        "validation": validation,
        "eligibility": eligibility,
        "claim_boundary": (
            "Replay-ready only when validation.ready_for_replay is true; "
            "derived records are not new online V2 decisions."
        ),
    }


def verify_dataset_manifest(manifest: dict) -> list[dict]:
    mismatches = []
    targets = {manifest["dataset"]: manifest["dataset_sha256"], **manifest["sources"]}
    for name, expected in targets.items():
        path = Path(name)
        actual = file_sha256(path) if path.exists() else None
        if actual != expected:
            mismatches.append({"path": name, "expected": expected, "actual": actual})
    return mismatches
