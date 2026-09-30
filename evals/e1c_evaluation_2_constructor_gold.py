"""Grader-only Gold check for the deterministic public constructor probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time

from evals.e1c_evaluation_2_admission import OUT as GRADER
from evals.e1c_evaluation_2_admission import materialize
from evals.e1c_evaluation_2_constructor_pilot import OUT as PILOT
from evals.e1c_evaluation_2_constructor_rule import OUT as BASE
from evals.e1c_evaluation_2_constructor_rule import source_from_public_issue
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_issue_input import OUT as ISSUE
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import (
    SOURCE_IDENTITY_SHELL,
    docker_command,
    validate_candidate,
    verified_local_image,
)

OUT = GRADER / "constructor-rule-discrimination-v1"


def run() -> dict:
    freeze = json.loads((PILOT / "freeze.json").read_text(encoding="utf-8"))
    instance_id = freeze["instance_id"]
    base_path = BASE / instance_id / "result.json"
    base = json.loads(base_path.read_text(encoding="utf-8"))
    execution = base["execution"]
    runs = execution["runs"]
    match = re.search(r"`([A-Za-z_]\w*)`\s+in\s+`[A-Za-z_]\w*\.__init__\(\)`", base["issue_quote"])
    if match is None:
        raise ValueError("base probe has no public constructor parameter")
    parameter = match.group(1)
    expected_error = f"unexpected keyword argument '{parameter}'"
    if (
        base.get("schema") != "e1c2-dev-constructor-rule-v1"
        or base.get("provider_calls") != 0
        or base.get("source_provenance") != "deterministic_public_boolean_constructor_rule_not_model_response"
        or not execution.get("network_none")
        or not execution.get("pull_never")
        or not execution.get("repeatable_nonsetup_failure")
        or len(runs) != 2
        or any(row["returncode"] != 1 or row["timed_out"] or expected_error not in row["log_tail"] for row in runs)
        or runs[0]["log_sha256"] != runs[1]["log_sha256"]
    ):
        raise ValueError("no repeated public constructor failure on frozen base")
    frozen_path = ISSUE / instance_id / "frozen_input_v3.json"
    if _sha(frozen_path) != base["input_sha256"]:
        raise ValueError("base and Gold public inputs differ")
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    source = source_from_public_issue(frozen["issue"], base["issue_quote"])
    candidate = validate_candidate(source, base["issue_quote"], frozen, workspace=SOURCE / instance_id)
    if candidate["probe_sha256"] != base["source_sha256"]:
        raise ValueError("Gold candidate differs from frozen base probe")
    admission_path = GRADER / instance_id / "gold.json"
    admission = json.loads(admission_path.read_text(encoding="utf-8"))
    if admission.get("phase_pass") is not True or admission.get("provider_calls") != 0:
        raise ValueError("official Gold admission has not passed")
    grader = materialize(instance_id)
    image = verified_local_image(instance_id)
    probe_path = BASE / instance_id / "execution" / f"{candidate['probe_sha256']}.py"
    command = docker_command(candidate, image, frozen["base_commit"], probe_path)
    command.remove("--read-only")  # Gold is applied inside the disposable container only.
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
        "schema": "e1c2-constructor-rule-gold-discrimination-v1", "instance_id": instance_id,
        "base_result_sha256": _sha(base_path), "gold_admission_sha256": _sha(admission_path),
        "gold_patch_sha256": _sha(grader / "gold.patch"), "probe_sha256": candidate["probe_sha256"],
        "source_provenance": "deterministic_public_boolean_constructor_rule_not_model_response",
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
