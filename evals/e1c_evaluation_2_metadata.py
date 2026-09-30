"""Fetch only frozen DEV12 task.yaml metadata from the official task tree."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_evaluation_2 import IDENTITY, ROOT
from evals.e1c_strict_v5_official_metadata import fetch_task_metadata

OUT = ROOT / ".codex/e1c/evaluation_2/dev12_metadata.json"


def acquire(identity_bytes: bytes, output: Path = OUT) -> dict:
    identity = json.loads(identity_bytes)
    tasks = identity["tasks"]
    revision = identity["source_revision"]
    if identity.get("role") != "development_only_never_independent_canary_or_fresh30" or len(tasks) != 12:
        raise ValueError("expected frozen DEV12 identity")
    rows = [fetch_task_metadata(row, revision) for row in tasks]
    if len({row["instance_id"] for row in rows}) != 12:
        raise ValueError("duplicate official task metadata")
    result = {
        "schema": "e1c-evaluation-2-dev12-official-metadata-v1",
        "cohort": "dev12",
        "identity_sha256": hashlib.sha256(identity_bytes).hexdigest(),
        "source_revision": revision,
        "task_content_inspected": False,
        "provider_calls": 0,
        "tasks": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = acquire(IDENTITY.read_bytes())
    print(json.dumps({"status": "metadata_acquired", "count": len(result["tasks"]), "output": str(OUT)}))
