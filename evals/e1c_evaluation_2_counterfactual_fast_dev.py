"""Reuse frozen old-DEV windows while still checking source, Git and image identity."""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess

from evals import e1c_evaluation_2_counterfactual_dev as study
from evals.e1c_evaluation_2_dev_pilot import ROOT, _sha
from evals.e1c_evaluation_2_source_contract import source_trees

OUT = ROOT / ".codex/e1c/evaluation_2/counterfactual-fast-dev-v1"
PROTOCOL = ROOT / "docs/research/E1C2_COUNTERFACTUAL_FAST_INPUT_2026-10-05.md"
_preflight = study.preflight


def verify_workspace(frozen, workspace):
    head = subprocess.check_output(["git", "-C", str(workspace), "rev-parse", "HEAD"], encoding="utf-8", timeout=30).strip()
    dirty = subprocess.check_output(["git", "-C", str(workspace), "status", "--porcelain", "--untracked-files=all"], encoding="utf-8", timeout=90).strip()
    if head != frozen["base_commit"] or dirty:
        raise ValueError("frozen production workspace no longer clean at base")
    list(source_trees(frozen, workspace))


def inputs():
    source = study.SOURCE
    freeze = json.loads((source / "freeze.json").read_bytes())
    state = json.loads((source / "state.json").read_bytes())
    if (state.get("status") != "completed" or freeze["fixed_denominator"] != 12
            or len(freeze["tasks"]) != 9 or [r["instance_id"] for r in state["rows"]] != [r["instance_id"] for r in freeze["tasks"]]
            or freeze["dev_v3_module_sha256"] != _sha(ROOT / "evals/e1c_evaluation_2_hybrid_dev_v3.py")):
        raise ValueError("complete unchanged upstream DEV v3 required")
    rows = []
    for row in freeze["tasks"]:
        iid = row["instance_id"]
        path = source / "inputs" / f"{iid}.json"
        if _sha(path) != row["input_sha256"]:
            raise ValueError("upstream frozen issue/window bytes changed")
        frozen, workspace = json.loads(path.read_bytes()), study.runtime.coverage.SOURCE / iid
        verify_workspace(frozen, workspace)
        image = study.runtime.verified_local_image(iid)
        if image != row["image_id"]:
            raise ValueError("upstream immutable image identity changed")
        rows.append((iid, frozen, path, workspace, image))
    return rows


def configure():
    study.OUT = OUT
    study.preflight = preflight
    study.dev.inputs = inputs
    study.configure()
    study.runtime.inputs, study.runtime.preflight = inputs, preflight


def preflight():
    configure()
    value = _preflight()
    study.runtime.preflight = preflight
    value.update({"schema": "e1c2-counterfactual-fast-input-dev-v1", "fast_adapter_sha256": _sha(ROOT / "evals/e1c_evaluation_2_counterfactual_fast_dev.py"),
                  "fast_protocol_sha256": _sha(PROTOCOL), "source_input_freeze_sha256": _sha(study.SOURCE / "freeze.json"),
                  "source_completed_state_sha256": _sha(study.SOURCE / "state.json"), "input_method_changed": False,
                  "source_integrity_rechecked": True, "zero_gate_sha256": _sha(ROOT / "data/e1c_evaluation_2_counterfactual_zero_gate.json")})
    gate = json.loads((ROOT / "data/e1c_evaluation_2_counterfactual_zero_gate.json").read_bytes())
    if gate.get("development_mechanism_gate_pass") is not True or gate.get("four_reference_tasks_retained") is not True:
        raise ValueError("zero-call mechanism gate has not passed")
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "gold"))
    args = parser.parse_args()
    configure()
    result = study.runtime.freeze() if args.command == "preflight" else asyncio.run(study.dev.run()) if args.command == "run" else study.runtime.grade()
    print(json.dumps(result, ensure_ascii=False))
