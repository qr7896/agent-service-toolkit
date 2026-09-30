"""Grader-only, zero-provider Gold discrimination of an optional-dependency DEV probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time

from evals.e1c_evaluation_2_admission import OUT as GRADER
from evals.e1c_evaluation_2_admission import materialize
from evals.e1c_evaluation_2_dev_pilot import TASKS, _save, _sha
from evals.e1c_evaluation_2_feedback_pilot import REPLAY, ROOT_OUT, _prior
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import (
    SOURCE_IDENTITY_SHELL,
    docker_command,
    issue_missing_optional_import,
    validate_candidate,
    verified_local_image,
)

BASE = ROOT_OUT / "e1c2-optional-dep-dev-diagnostic-v2"
OUT = GRADER / "optional-dep-discrimination-v1"


def run(instance_id: str) -> dict:
    if instance_id not in TASKS:
        raise ValueError("Gold discriminator requires a frozen DEV pilot task")
    base_path = BASE / instance_id / "result.json"
    base = json.loads(base_path.read_text(encoding="utf-8"))
    execution = base["execution"]
    if (
        base.get("schema") != "e1c2-optional-dep-dev-diagnostic-v2"
        or base.get("provider_calls") != 0
        or not execution.get("network_none")
        or not execution.get("pull_never")
        or not execution.get("repeatable_nonsetup_failure")
        or len(execution.get("runs", [])) != 2
    ):
        raise ValueError("no repeatable, isolated base failure to discriminate")
    frozen_path = ISSUE / instance_id / "frozen_input_v3.json"
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    if base["issue_input_sha256"] != _sha(frozen_path):
        raise ValueError("base and Gold issue inputs differ")
    missing_import = issue_missing_optional_import(frozen)
    if not missing_import or missing_import != base["missing_optional_import"]:
        raise ValueError("optional dependency precondition changed")
    replay = json.loads(REPLAY.read_text(encoding="utf-8"))
    source, raw, prior_sha = _prior(instance_id, replay)
    candidate = validate_candidate(source, json.loads(raw)["issue_quote"], frozen, workspace=SOURCE / instance_id)
    if prior_sha != base["prior_response_sha256"] or candidate["probe_sha256"] != base["probe_sha256"]:
        raise ValueError("Gold candidate differs from frozen base candidate")
    admission = json.loads((GRADER / instance_id / "gold.json").read_text(encoding="utf-8"))
    if admission.get("phase_pass") is not True or admission.get("provider_calls") != 0:
        raise ValueError("official Gold admission has not passed")
    grader = materialize(instance_id)
    image = verified_local_image(instance_id)
    base_execution = BASE / instance_id / "execution"
    probe_path = base_execution / f"{candidate['probe_sha256']}.py"
    blocker_dir = base_execution / "optional_missing"
    command = docker_command(candidate, image, frozen["base_commit"], probe_path,
                             blocked_import_dir=blocker_dir)
    command.remove("--read-only")  # Gold patch changes only the disposable container's source tree.
    command[command.index("--name") + 1] = "e1c2-gold-" + candidate["probe_sha256"][:16]
    gold_marker = b"E1C2_GOLD_PATCH_APPLIED:PASS"
    command[-3] = (
        SOURCE_IDENTITY_SHELL
        + 'cd /testbed; git apply --check /e1c2_gold.patch && git apply /e1c2_gold.patch || exit 91; '
        + 'echo "E1C2_GOLD_PATCH_APPLIED:PASS"; '
        + "/opt/miniconda3/envs/testbed/bin/python -X utf8 /e1c2_probe.py"
    )
    command[command.index(image):command.index(image)] = [
        "--mount", f"type=bind,source={(grader / 'gold.patch').resolve()},target=/e1c2_gold.patch,readonly",
    ]
    destination = OUT / instance_id
    log_path = destination / "gold.log"
    result_path = destination / "result.json"
    if log_path.exists() or result_path.exists():
        raise FileExistsError("Gold discriminator already started; no silent retry")
    destination.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with log_path.open("xb") as log:
        try:
            completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=90, check=False)
            returncode, timed_out = completed.returncode, False
        except subprocess.TimeoutExpired:
            returncode, timed_out = None, True
            subprocess.run(["docker", "rm", "-f", command[command.index("--name") + 1]],
                           capture_output=True, timeout=30, check=False)
    log_bytes = log_path.read_bytes()
    result = {
        "schema": "e1c2-optional-dep-gold-discrimination-v1",
        "instance_id": instance_id,
        "base_result_sha256": _sha(base_path),
        "gold_admission_sha256": _sha(GRADER / instance_id / "gold.json"),
        "gold_patch_sha256": _sha(grader / "gold.patch"),
        "probe_sha256": candidate["probe_sha256"],
        "missing_optional_import": missing_import,
        "network_none": True, "pull_never": True,
        "returncode": returncode, "timed_out": timed_out,
        "gold_patch_applied": gold_marker in log_bytes,
        "gold_discriminating": returncode == 0 and gold_marker in log_bytes and not timed_out,
        "log_sha256": hashlib.sha256(log_bytes).hexdigest(),
        "log_bytes": len(log_bytes),
        "duration_seconds": round(time.monotonic() - started, 3),
        "provider_calls": 0, "grader_only": True, "trusted_reproducer": False,
    }
    _save(result_path, result)
    return {key: result[key] for key in (
        "instance_id", "returncode", "timed_out", "gold_patch_applied",
        "gold_discriminating", "provider_calls", "trusted_reproducer",
    )}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instance_id")
    args = parser.parse_args()
    print(json.dumps(run(args.instance_id), ensure_ascii=False))


if __name__ == "__main__":
    main()
