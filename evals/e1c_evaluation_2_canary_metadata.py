"""Read only official task.yaml metadata after E1-C canary identity selection."""

from __future__ import annotations

import json

from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_canary_select import FREEZE, IDENTITY, method
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_strict_v5_official_metadata import fetch_task_metadata

OUT = ROOT / ".codex/e1c/evaluation_2/canary-v1/metadata.json"


def acquire() -> dict:
    identity = json.loads(IDENTITY.read_bytes())
    if (
        json.loads(FREEZE.read_bytes()) != method()
        or identity.get("method_freeze_sha256") != _sha(FREEZE)
        or identity.get("role") != "independent_canary_one_shot_no_replacement"
        or len(identity.get("tasks", [])) != 3
    ):
        raise ValueError("canary method or metadata-only identity changed")
    rows = [fetch_task_metadata(task, identity["source_revision"]) for task in identity["tasks"]]
    if [row["instance_id"] for row in rows] != [row["instance_id"] for row in identity["tasks"]]:
        raise ValueError("official metadata differs from frozen identity")
    value = {
        "schema": "e1c2-canary-official-metadata-v1",
        "identity_sha256": _sha(IDENTITY),
        "source_revision": identity["source_revision"],
        "task_content_inspected": False,
        "provider_calls": 0,
        "tasks": rows,
    }
    if OUT.exists():
        if json.loads(OUT.read_bytes()) != value:
            raise ValueError("existing canary metadata differs")
    else:
        _save(OUT, value)
    return value


if __name__ == "__main__":
    result = acquire()
    print(json.dumps({"tasks": [{key: row[key] for key in ("instance_id", "repo", "base_commit", "image")} for row in result["tasks"]], "provider_calls": 0}, indent=2))
