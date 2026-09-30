"""Freeze new DEV inputs after exact public CLI-option lexical localization."""

from __future__ import annotations

import argparse
import hashlib
import json

from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_issue_input import SOURCE, TREE
from evals.e1c_evaluation_2_metadata import OUT as METADATA
from evals.e1c_evaluation_2_probe import freeze_input
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

OUT = ROOT / ".codex/e1c/evaluation_2/issue-only-v4-index.json"


def run() -> dict:
    metadata = {row["instance_id"]: row for row in json.loads(METADATA.read_bytes())["tasks"]}
    tree = json.loads(TREE.read_text(encoding="utf-8"))
    rows = []
    for old_path in sorted(ISSUE.glob("*/frozen_input_v3.json")):
        instance_id = old_path.parent.name
        if instance_id not in metadata:
            raise ValueError("unknown DEV task in prior input set")
        issue_path = old_path.parent / "problem_statement.md"
        raw = issue_path.read_bytes()
        expected_blob = tree["sha"][f"tasks/{instance_id}/problem_statement.md"]
        if hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest() != expected_blob:
            raise ValueError("public issue blob changed")
        frozen = freeze_input(
            raw.decode("utf-8"), SOURCE / instance_id,
            metadata[instance_id]["base_commit"], balanced=True,
        )
        frozen.pop("input_sha256")
        frozen["schema"] = "e1c-evaluation-2-probe-input-v4"
        frozen["input_sha256"] = audit_repair_visible_payload(frozen)
        new_path = old_path.parent / "frozen_input_v4.json"
        if new_path.is_file():
            if json.loads(new_path.read_text(encoding="utf-8")) != frozen:
                raise ValueError("existing v4 DEV input differs; no overwrite")
        else:
            _save(new_path, frozen)
        rows.append({
            "instance_id": instance_id, "prior_input_sha256": _sha(old_path),
            "v4_input_sha256": _sha(new_path), "candidate_paths": frozen["candidate_paths"],
            "provider_calls": 0,
        })
    if len(rows) != 9:
        raise ValueError(f"expected nine admitted DEV issue inputs, found {len(rows)}")
    value = {"schema": "e1c2-dev-issue-input-v4-index", "rows": rows, "provider_calls": 0}
    if OUT.is_file():
        if json.loads(OUT.read_text(encoding="utf-8")) != value:
            raise ValueError("existing v4 index differs; no overwrite")
    else:
        _save(OUT, value)
    return {"count": len(rows), "provider_calls": 0, "index": str(OUT)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run",))
    parser.parse_args()
    print(json.dumps(run(), ensure_ascii=False))


if __name__ == "__main__":
    main()
