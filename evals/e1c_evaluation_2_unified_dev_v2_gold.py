"""Grader-only Gold discrimination for every repeated failure in frozen Flash DEV v2."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time

from evals.e1c_evaluation_2_admission import OUT as GRADER
from evals.e1c_evaluation_2_admission import materialize
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_probe import SOURCE_IDENTITY_SHELL, docker_command, verified_local_image
from evals.e1c_evaluation_2_unified_dev_v2 import base

OUT = GRADER / "unified-dev-v2-discrimination"
MARKER = b"E1C2_GOLD_PATCH_APPLIED:PASS"


def _eligible(row: dict, execution: dict) -> bool:
    runs = execution.get("runs", [])
    return bool(
        row.get("status") == "executed"
        and (row.get("repeatable_failure_candidate") or row.get("repeatable_nonsetup_failure"))
        and len(runs) == 2
        and runs[0]["log_sha256"] == runs[1]["log_sha256"]
        and all(not item["timed_out"] and item["returncode"] not in {None, 0, 90, 125, 126, 127} for item in runs)
        and execution.get("network_none") is True
        and execution.get("pull_never") is True
    )


def run() -> dict:
    freeze_path = base.FREEZE
    state_path = base.OUT / "state.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("status") != "completed" or freeze != base.preflight():
        raise ValueError("unified Flash DEV run is not sealed and unchanged")
    rows = {row["instance_id"]: row for row in state["rows"]}
    outcomes = []
    for frozen_row in freeze["tasks"]:
        instance_id = frozen_row["instance_id"]
        row = rows[instance_id]
        execution_path = base.OUT / instance_id / "execution.json"
        if not execution_path.is_file():
            continue
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        if not _eligible(row, execution):
            continue
        candidate_path = base.OUT / instance_id / "candidate.json"
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        if (
            candidate.get("safe_static_check") is not True
            or candidate["probe_sha256"] != execution["probe_sha256"]
            or frozen_row["image_id"] != verified_local_image(instance_id)
            or execution["image"] != frozen_row["image_id"]
        ):
            raise ValueError(f"base candidate/image identity differs: {instance_id}")
        admission_path = GRADER / instance_id / "gold.json"
        admission = json.loads(admission_path.read_text(encoding="utf-8"))
        if admission.get("phase_pass") is not True or admission.get("provider_calls") != 0:
            raise ValueError(f"official Gold admission missing: {instance_id}")
        grader = materialize(instance_id)
        probe_path = base.OUT / instance_id / "execution" / f"{candidate['probe_sha256']}.py"
        if _sha(probe_path) != candidate["probe_sha256"]:
            raise ValueError("base probe artifact changed")
        blocked_dir = None
        if execution.get("missing_optional_import"):
            blocked_dir = probe_path.parent / "optional_missing"
        command = docker_command(
            candidate, frozen_row["image_id"], execution["base_commit"], probe_path,
            blocked_import_dir=blocked_dir,
        )
        command.remove("--read-only")
        command[command.index("--name") + 1] = "e1c2-gold-" + candidate["probe_sha256"][:16]
        command[-3] = (
            SOURCE_IDENTITY_SHELL
            + 'cd /testbed; git apply --check /e1c2_gold.patch && git apply /e1c2_gold.patch || exit 91; '
            + 'echo "E1C2_GOLD_PATCH_APPLIED:PASS"; '
            + "/opt/miniconda3/envs/testbed/bin/python -X utf8 /e1c2_probe.py"
        )
        image_index = command.index(frozen_row["image_id"])
        command[image_index:image_index] = [
            "--mount", f"type=bind,source={(grader / 'gold.patch').resolve()},target=/e1c2_gold.patch,readonly",
        ]
        destination = OUT / instance_id
        log_path = destination / "gold.log"
        result_path = destination / "result.json"
        if log_path.exists() or result_path.exists():
            raise FileExistsError(f"Gold discriminator already started: {instance_id}")
        destination.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        with log_path.open("xb") as log:
            try:
                completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=90, check=False)
                returncode, timed_out = completed.returncode, False
            except subprocess.TimeoutExpired:
                returncode, timed_out = None, True
                subprocess.run(
                    ["docker", "rm", "-f", command[command.index("--name") + 1]],
                    capture_output=True, timeout=30, check=False,
                )
        raw = log_path.read_bytes()
        result = {
            "schema": "e1c2-unified-dev-v2-gold-discrimination-v1", "instance_id": instance_id,
            "freeze_sha256": _sha(freeze_path), "base_execution_sha256": _sha(execution_path),
            "candidate_sha256": _sha(candidate_path), "gold_admission_sha256": _sha(admission_path),
            "gold_patch_sha256": _sha(grader / "gold.patch"), "probe_sha256": candidate["probe_sha256"],
            "network_none": True, "pull_never": True,
            "returncode": returncode, "timed_out": timed_out,
            "gold_patch_applied": MARKER in raw,
            "gold_discriminating": returncode == 0 and MARKER in raw and not timed_out,
            "log_sha256": hashlib.sha256(raw).hexdigest(), "log_bytes": len(raw),
            "duration_seconds": round(time.monotonic() - started, 3),
            "provider_calls": 0, "grader_only": True,
            "trusted_reproducer": False,  # Semantic issue alignment is a separate gate.
        }
        _save(result_path, result)
        summary = {key: result[key] for key in (
            "instance_id", "returncode", "gold_patch_applied", "gold_discriminating", "trusted_reproducer",
        )}
        outcomes.append(summary)
        print(json.dumps(summary, ensure_ascii=False), flush=True)
    return {"attempted": len(outcomes), "gold_discriminating": sum(row["gold_discriminating"] for row in outcomes)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run",))
    parser.parse_args()
    print(json.dumps(run(), ensure_ascii=False))


if __name__ == "__main__":
    main()
