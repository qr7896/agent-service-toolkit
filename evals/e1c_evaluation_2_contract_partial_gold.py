"""Score saved B-prefix probes without relabeling its interrupted provider run."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from evals import e1c_evaluation_2_contract_ab_dev as experiment
from evals.e1c_evaluation_2_admission import materialize
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_probe import SOURCE_IDENTITY_SHELL, docker_command, verified_local_image


def run() -> dict:
    root = experiment.OUT / "B"
    freeze = json.loads((root / "freeze.json").read_bytes())
    state = json.loads((root / "state.json").read_bytes())
    if state["status"] != "interrupted_no_auto_retry" or freeze != experiment.preflight("B"):
        raise ValueError("partial grader requires the unchanged interrupted B run")
    rows = {row["instance_id"]: row for row in state["rows"]}
    results = []
    for frozen_row in freeze["tasks"]:
        iid = frozen_row["instance_id"]
        row = rows.get(iid, {})
        if row.get("status") != "executed" or row.get("control_pass") is not True or not (
            row.get("repeatable_failure_candidate") or row.get("repeatable_nonsetup_failure")
        ):
            continue
        candidate_path, execution_path = root / iid / "candidate.json", root / iid / "execution.json"
        candidate, execution = json.loads(candidate_path.read_bytes()), json.loads(execution_path.read_bytes())
        image = verified_local_image(iid)
        if image != frozen_row["image_id"] or candidate["probe_sha256"] != execution["probe_sha256"]:
            raise ValueError("saved candidate/image changed")
        probe = root / iid / "execution" / f"{candidate['probe_sha256']}.py"
        if _sha(probe) != candidate["probe_sha256"]:
            raise ValueError("saved probe changed")
        grader = materialize(iid)
        command = docker_command(candidate, image, execution["base_commit"], probe,
                                 blocked_import_dir=probe.parent / "optional_missing" if execution.get("missing_optional_import") else None)
        command.remove("--read-only")
        name = "e1c2-partial-gold-" + candidate["probe_sha256"][:16]
        command[command.index("--name") + 1] = name
        command[-3] = (SOURCE_IDENTITY_SHELL + 'cd /testbed; git apply --check /e1c2_gold.patch && git apply /e1c2_gold.patch || exit 91; '
                       + 'echo "E1C2_GOLD_PATCH_APPLIED:PASS"; /opt/miniconda3/envs/testbed/bin/python -X utf8 /e1c2_probe.py')
        index = command.index(image)
        command[index:index] = ["--mount", f"type=bind,source={(grader / 'gold.patch').resolve()},target=/e1c2_gold.patch,readonly"]
        destination = root / "partial-gold-discrimination" / iid
        destination.mkdir(parents=True, exist_ok=True)
        log_path, result_path = destination / "gold.log", destination / "result.json"
        if log_path.exists() or result_path.exists():
            raise FileExistsError("partial Gold evidence already exists; no silent repeat")
        with log_path.open("xb") as log:
            try:
                outcome = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=90, check=False)
                code, timed_out = outcome.returncode, False
            except subprocess.TimeoutExpired:
                code, timed_out = None, True
                subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=30, check=False)
        raw = log_path.read_bytes()
        applied = b"E1C2_GOLD_PATCH_APPLIED:PASS" in raw
        result = {"schema": "e1c2-contract-partial-gold-v1", "instance_id": iid,
                  "source_arm_status": state["status"], "fixed_denominator": 12, "original_state_sha256": _sha(root / "state.json"),
                  "freeze_sha256": _sha(root / "freeze.json"), "candidate_sha256": _sha(candidate_path),
                  "base_execution_sha256": _sha(execution_path), "probe_sha256": candidate["probe_sha256"],
                  "grader_sha256": _sha(Path(__file__)), "returncode": code, "timed_out": timed_out,
                  "gold_patch_applied": applied, "gold_discriminating": code == 0 and applied and not timed_out,
                  "log_sha256": hashlib.sha256(raw).hexdigest(), "network_none": True, "pull_never": True,
                  "provider_calls": 0, "trusted_reproducer": False}
        _save(result_path, result)
        results.append(result)
        print(json.dumps({key: result[key] for key in ("instance_id", "returncode", "gold_discriminating")}), flush=True)
    return {"attempted": len(results), "gold_discriminating": sum(row["gold_discriminating"] for row in results),
            "source_arm_status": state["status"], "comparison_complete": False, "provider_calls": 0}


if __name__ == "__main__":
    print(json.dumps(run()))
