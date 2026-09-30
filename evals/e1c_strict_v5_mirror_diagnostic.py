"""Non-authoritative GHCR mirror diagnostics for the frozen strict-v5 canary.

This module never contributes to admission. It exists only to separate Docker
runner failures from Docker Hub transport failures.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

import yaml

from evals.e1c_admission import ROOT, _official_grader, source_identity
from evals.e1c_strict_v5_verification import FILES, GRADER_ROOT, MATERIALIZED_ROOT

OUT_ROOT = ROOT / ".codex" / "e1c" / "strict-v5" / "mirror-diagnostic-v1"
MIRROR_PREFIX = "ghcr.io/epoch-research/swe-bench.eval.x86_64."


def mirror_image(instance_id: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+", instance_id):
        raise ValueError("unsafe instance id")
    return f"{MIRROR_PREFIX}{instance_id}:latest"


def _stage(instance_id: str) -> Path:
    source_task = MATERIALIZED_ROOT / instance_id / "task.yaml"
    grader = GRADER_ROOT / instance_id
    if not source_task.is_file() or not grader.is_dir():
        raise FileNotFoundError(instance_id)
    destination = OUT_ROOT / "input" / instance_id
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_task, destination / "task.yaml")
    for name in FILES:
        candidate = grader / name
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        shutil.copy2(candidate, destination / name)
    return destination


def run_phase(instance_id: str, phase: str, timeout: int = 1800) -> dict:
    if phase not in {"base", "gold"}:
        raise ValueError("phase must be base or gold")
    task_dir = _stage(instance_id)
    task = yaml.safe_load((task_dir / "task.yaml").read_text(encoding="utf-8"))
    tests = json.loads((task_dir / "tests.json").read_text(encoding="utf-8"))
    image = mirror_image(instance_id)
    digest = subprocess.check_output(
        ["docker", "image", "inspect", image, "--format", "{{index .RepoDigests 0}}"],
        text=True,
        timeout=30,
    ).strip()
    artifact_dir = OUT_ROOT / "artifacts" / instance_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    log_path = artifact_dir / f"{phase}.log"
    result_path = artifact_dir / f"{phase}.json"
    if log_path.exists() or result_path.exists():
        raise FileExistsError("mirror diagnostic phase already exists; no silent retry")
    expected = task["base_commit"]
    script = (
        "set -e; "
        "git config --global --add safe.directory /testbed; "
        "git -C /testbed diff --quiet; git -C /testbed diff --cached --quiet; "
        'head="$(git -C /testbed rev-parse HEAD)"; '
        f'git -C /testbed merge-base --is-ancestor "{expected}" "$head"; '
        f'expected_tree="$(git -C /testbed rev-parse "{expected}^{{tree}}")"; '
        'actual_tree="$(git -C /testbed rev-parse HEAD^{tree})"; '
        'echo "E1C_CONTAINER_HEAD:$head"; '
        'echo "E1C_EXPECTED_TREE:$expected_tree"; '
        'echo "E1C_ACTUAL_TREE:$actual_tree"; '
        "cd /testbed; "
        + (
            "git apply --check /admission/gold.patch; git apply /admission/gold.patch; "
            if phase == "gold"
            else ""
        )
        + "bash /admission/eval.sh"
    )
    command = [
        "docker",
        "run",
        "--rm",
        "--platform",
        "linux/amd64",
        "--network",
        "none",
        "--mount",
        f"type=bind,source={task_dir},target=/admission,readonly",
        image,
        "bash",
        "-lc",
        script,
    ]
    started = time.monotonic()
    timed_out = False
    with log_path.open("wb") as log:
        try:
            exit_code = subprocess.run(
                command,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
            ).returncode
        except subprocess.TimeoutExpired:
            timed_out, exit_code = True, None
    log_bytes = log_path.read_bytes()
    identity = source_identity(log_bytes, (task_dir / "gold.patch", task_dir / "test.patch"))
    get_logs_eval, test_maintained, test_passed, resolve_case, TestSpec = _official_grader()
    spec = TestSpec(
        instance_id=instance_id,
        image=image,
        eval_script_list=[],
        repo=task["repo"],
        version=str(task.get("version", "")),
        FAIL_TO_PASS=tests["FAIL_TO_PASS"],
        PASS_TO_PASS=tests["PASS_TO_PASS"],
        log_parser=task["log_parser"],
    )
    statuses, valid_log = get_logs_eval(spec, str(log_path)) if not timed_out else ({}, False)
    f2p_pass = sum(test_passed(name, statuses) for name in tests["FAIL_TO_PASS"])
    f2p_explicit_fail = sum(
        (key := resolve_case(name, statuses)) is not None
        and statuses[key] in {"FAILED", "ERROR"}
        for name in tests["FAIL_TO_PASS"]
    )
    p2p_maintained = sum(test_maintained(name, statuses) for name in tests["PASS_TO_PASS"])
    phase_pass = (
        identity["source_identity_valid"] and valid_log and bool(f2p_explicit_fail)
        if phase == "base"
        else (
            identity["source_identity_valid"]
            and valid_log
            and exit_code == 0
            and f2p_pass == len(tests["FAIL_TO_PASS"])
            and p2p_maintained == len(tests["PASS_TO_PASS"])
        )
    )
    result = {
        "schema": "e1c-strict-v5-mirror-diagnostic-v1",
        "authoritative_for_admission": False,
        "instance_id": instance_id,
        "phase": phase,
        "mirror_image": image,
        "mirror_digest": digest,
        "source_identity_valid": identity["source_identity_valid"],
        "valid_log": valid_log,
        "exit_code": exit_code,
        "timeout": timed_out,
        "phase_pass": phase_pass,
        "f2p_pass": f2p_pass,
        "f2p_explicit_fail": f2p_explicit_fail,
        "f2p_total": len(tests["FAIL_TO_PASS"]),
        "p2p_maintained": p2p_maintained,
        "p2p_total": len(tests["PASS_TO_PASS"]),
        "log_sha256": hashlib.sha256(log_bytes).hexdigest(),
        "duration_seconds": round(time.monotonic() - started, 3),
        "provider_calls": 0,
        "repair_visible": False,
    }
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("instance_id")
    parser.add_argument("phase", choices=("base", "gold"))
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    print(json.dumps(run_phase(args.instance_id, args.phase, args.timeout), indent=2))
