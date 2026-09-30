"""Grader-only Gold discrimination of a sealed public-traceback DEV probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time

from evals.e1c_evaluation_2_admission import OUT as GRADER
from evals.e1c_evaluation_2_admission import materialize
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import (
    SOURCE_IDENTITY_SHELL,
    docker_command,
    validate_candidate,
    verified_local_image,
)
from evals.e1c_evaluation_2_traceback_pilot import OUT as PILOT
from evals.e1c_evaluation_2_traceback_replay import OUT as BASE

OUT = GRADER / "traceback-discrimination-v1"


def run() -> dict:
    freeze = json.loads((PILOT / "freeze.json").read_text(encoding="utf-8"))
    instance_id = freeze["instance_id"]
    base_path = BASE / instance_id / "result.json"
    base = json.loads(base_path.read_text(encoding="utf-8"))
    execution = base["execution"]
    quote = base["replacement_quote"]
    runs = execution["runs"]
    if (
        base.get("schema") != "e1c2-dev-traceback-replay-v1"
        or base.get("provider_calls") != 0
        or not execution.get("network_none")
        or not execution.get("pull_never")
        or not execution.get("repeatable_nonsetup_failure")
        or len(runs) != 2
        or any(row["returncode"] != 1 or row["timed_out"] or quote not in row["log_tail"] for row in runs)
        or runs[0]["log_sha256"] != runs[1]["log_sha256"]
    ):
        raise ValueError("no repeated exact public exception on frozen base")
    frozen_path = ISSUE / instance_id / "frozen_input_v3.json"
    if _sha(frozen_path) != base["input_sha256"]:
        raise ValueError("base and Gold public inputs differ")
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    response_path = PILOT / "response.json"
    if _sha(response_path) != base["response_sha256"]:
        raise ValueError("sealed model response differs from base replay")
    response = json.loads(response_path.read_text(encoding="utf-8"))
    source = json.loads(response["raw"])["source"]
    candidate = validate_candidate(source, quote, frozen, workspace=SOURCE / instance_id)
    if candidate["probe_sha256"] != base["probe_sha256"]:
        raise ValueError("Gold candidate differs from base probe")
    admission_path = GRADER / instance_id / "gold.json"
    admission = json.loads(admission_path.read_text(encoding="utf-8"))
    if admission.get("phase_pass") is not True or admission.get("provider_calls") != 0:
        raise ValueError("official Gold admission has not passed")
    grader = materialize(instance_id)
    image = verified_local_image(instance_id)
    probe_path = BASE / instance_id / "execution" / f"{candidate['probe_sha256']}.py"
    command = docker_command(candidate, image, frozen["base_commit"], probe_path)
    command.remove("--read-only")  # The disposable container receives the Gold patch.
    command[command.index("--name") + 1] = "e1c2-gold-" + candidate["probe_sha256"][:16]
    marker = b"E1C2_GOLD_PATCH_APPLIED:PASS"
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
    raw = log_path.read_bytes()
    gold_discriminating = returncode == 0 and marker in raw and not timed_out
    result = {
        "schema": "e1c2-traceback-gold-discrimination-v1", "instance_id": instance_id,
        "base_result_sha256": _sha(base_path), "gold_admission_sha256": _sha(admission_path),
        "gold_patch_sha256": _sha(grader / "gold.patch"), "probe_sha256": candidate["probe_sha256"],
        "network_none": True, "pull_never": True,
        "returncode": returncode, "timed_out": timed_out,
        "gold_patch_applied": marker in raw, "gold_discriminating": gold_discriminating,
        "log_sha256": hashlib.sha256(raw).hexdigest(), "log_bytes": len(raw),
        "duration_seconds": round(time.monotonic() - started, 3),
        "provider_calls": 0, "grader_only": True, "trusted_reproducer": gold_discriminating,
    }
    _save(result_path, result)
    return {key: result[key] for key in (
        "instance_id", "returncode", "timed_out", "gold_patch_applied",
        "gold_discriminating", "provider_calls", "trusted_reproducer",
    )}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run",))
    parser.parse_args()
    print(json.dumps(run(), ensure_ascii=False))


if __name__ == "__main__":
    main()
