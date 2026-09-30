"""Freeze strict-v7 mechanism identity before selecting a new canary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT

OUT = ROOT / "data" / "e1c_strict_v7_prereg.json"
BOUNDARY = ROOT / "data" / "e1c_strict_v7_selection_boundary.json"
MECHANISM_FILES = (
    ROOT / "evals" / "e1c_strict_v5_boundary.py",
    ROOT / "evals" / "e1c_strict_v6_probe.py",
    ROOT / "evals" / "e1c_strict_v7_witness_ir.py",
    ROOT / "evals" / "e1c_strict_v7_probe.py",
    ROOT / "evals" / "e1c_strict_v7_runner.py",
)


def _file_identity(path: Path) -> dict:
    raw = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
    }


def build() -> dict:
    if not BOUNDARY.is_file():
        raise RuntimeError("strict-v7 selection boundary must exist before mechanism prereg")
    boundary_raw = BOUNDARY.read_bytes()
    boundary = json.loads(boundary_raw.decode("utf-8"))
    if boundary.get("canary_selected") is not False:
        raise RuntimeError("strict-v7 canary must remain unselected during mechanism freeze")
    files = [_file_identity(path) for path in MECHANISM_FILES]
    mechanism_sha = hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    value = {
        "schema": "e1c-strict-v7-reproducer-prereg-v1",
        "provider_calls": 0,
        "live_model_run": False,
        "task_content_selected_after_mechanism_freeze": True,
        "canary_selected_at_freeze": False,
        "parent_v6_seal": "data/e1c_strict_v6_prelive_seal.json",
        "prior_canary_reuse_allowed": False,
        "selection_salt": "e1c-strict-v7-independent-canary",
        "canary_task_count": 3,
        "minimum_candidate_reproducer_tasks": 2,
        "minimum_trusted_reproducers": 2,
        "live_allowed_before_admission": False,
        "mechanism_files": files,
        "mechanism_sha256": mechanism_sha,
        "selection_boundary_sha256": hashlib.sha256(boundary_raw).hexdigest(),
        "supported_candidate_kinds": [
            "call_result",
            "python_scenario",
            "state_transition",
            "artifact_predicate",
        ],
        "currently_executable_kinds": ["call_result", "python_scenario"],
        "unsupported_or_unresolved_behavior": "fail_closed_no_executable_reproducer",
        "development_replay_is_independent_evidence": False,
    }
    value["prereg_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value


def write(output: Path = OUT) -> dict:
    value = build()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


if __name__ == "__main__":
    print(json.dumps(write(), ensure_ascii=False, indent=2))
