"""Grade one E1-C candidate patch in a fresh official SWE-bench container."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml

from evals.e1c_admission import PARSER_COMMIT, ROOT, TASKS, _official_grader, source_identity


def grade(
    instance_id: str, stage: str, patch_path: Path, output_dir: Path, timeout: int = 1800
) -> dict:
    if sys.platform == "win32" and not sys.flags.utf8_mode:
        raise RuntimeError("Windows SWE-bench parsing requires python -X utf8")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", instance_id) or not re.fullmatch(
        r"[A-Za-z0-9_-]+", stage
    ):
        raise ValueError("unsafe task id or stage")
    task_dir = TASKS / instance_id
    task = yaml.safe_load((task_dir / "task.yaml").read_text(encoding="utf-8"))
    tests = json.loads((task_dir / "tests.json").read_text(encoding="utf-8"))
    expected = task["base_commit"]
    image = task["image"]
    if task["instance_id"] != instance_id or not re.fullmatch(r"[0-9a-f]{40}", expected):
        raise ValueError("task identity mismatch")
    if not re.fullmatch(r"swebench/[A-Za-z0-9_.-]+:latest", image):
        raise ValueError("nonofficial image")
    if subprocess.run(
        ["docker", "image", "inspect", image], capture_output=True, check=False
    ).returncode:
        raise RuntimeError("official image must be pulled before grading")
    admission = ROOT / ".codex" / "e1c" / "admission_v2" / instance_id
    base = json.loads((admission / "base.json").read_text(encoding="utf-8"))
    gold = json.loads((admission / "gold.json").read_text(encoding="utf-8"))
    image_digest = subprocess.check_output(
        ["docker", "image", "inspect", image, "--format", "{{index .RepoDigests 0}}"], text=True
    ).strip()
    if not (base["phase_pass"] and gold["phase_pass"] and image_digest == base["image_digest"] == gold["image_digest"]):
        raise RuntimeError("current image digest differs from admitted source identity")
    patch_path = patch_path.resolve()
    if not patch_path.is_file():
        raise FileNotFoundError(patch_path)
    patch_data = patch_path.read_bytes()
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / f"grade.{stage}.log"
    result_path = output_dir / f"grade.{stage}.json"
    if log_path.exists() or result_path.exists():
        raise FileExistsError("grade artifact already exists; no silent retry")
    source_check = (
        "set -e; git config --global --add safe.directory /testbed; "
        "git -C /testbed diff --quiet; git -C /testbed diff --cached --quiet; "
        'head="$(git -C /testbed rev-parse HEAD)"; '
        f'git -C /testbed merge-base --is-ancestor "{expected}" "$head"; '
        f'base_tree="$(git -C /testbed rev-parse "{expected}^{{tree}}")"; '
        'actual_tree="$(git -C /testbed rev-parse HEAD^{tree})"; '
        'echo "E1C_CONTAINER_HEAD:$head"; echo "E1C_EXPECTED_TREE:$base_tree"; echo "E1C_ACTUAL_TREE:$actual_tree"; '
        'while IFS= read -r file; do '
        'echo "E1C_IMAGE_DIFF_PATH:$file"; '
        'case "$file" in setup.py|tox.ini) ;; *) exit 81;; esac; '
        f'done < <(git -C /testbed diff --name-only "{expected}" HEAD); cd /testbed; '
    )
    script = (
        source_check
        + ("git apply --check /candidate.patch; git apply /candidate.patch; " if patch_data else "")
        + "bash /admission/eval.sh"
    )
    container_name = f"e1c-grade-{instance_id}-{stage}"
    command = [
        "docker",
        "run",
        "--rm",
        "--platform",
        "linux/amd64",
        "--network",
        "none",
        "--name",
        container_name,
        "--mount",
        f"type=bind,source={task_dir},target=/admission,readonly",
    ]
    if patch_data:
        command += ["--mount", f"type=bind,source={patch_path},target=/candidate.patch,readonly"]
    command += [image, "bash", "-lc", script]
    started = time.monotonic()
    timed_out = False
    with log_path.open("wb") as log:
        try:
            exit_code = subprocess.run(
                command, stdout=log, stderr=subprocess.STDOUT, timeout=timeout, check=False
            ).returncode
        except subprocess.TimeoutExpired:
            timed_out, exit_code = True, None
            subprocess.run(
                ["docker", "rm", "-f", container_name], capture_output=True, timeout=30, check=False
            )
    log_data = log_path.read_bytes()

    identity = source_identity(log_data, (patch_path, task_dir / "test.patch"))
    source_match = identity["source_identity_valid"]
    get_logs_eval, test_maintained, test_passed, _, TestSpec = _official_grader()
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
    p2p_maintained = sum(test_maintained(name, statuses) for name in tests["PASS_TO_PASS"])
    resolved = (
        source_match
        and valid_log
        and exit_code == 0
        and f2p_pass == len(tests["FAIL_TO_PASS"])
        and p2p_maintained == len(tests["PASS_TO_PASS"])
    )
    result = {
        "schema": "e1c-docker-grade-v2",
        "instance_id": instance_id,
        "stage": stage,
        "official_parser_commit": PARSER_COMMIT,
        "image": image,
        "image_digest": image_digest,
        "candidate_patch_sha256": hashlib.sha256(patch_data).hexdigest(),
        "base_commit": expected,
        **identity,
        "command": command,
        "exit_code": exit_code,
        "timeout": timed_out,
        "duration_seconds": round(time.monotonic() - started, 3),
        "valid_log": valid_log,
        "parsed_test_count": len(statuses),
        "f2p_pass": f2p_pass,
        "f2p_total": len(tests["FAIL_TO_PASS"]),
        "p2p_maintained": p2p_maintained,
        "p2p_total": len(tests["PASS_TO_PASS"]),
        "resolved": resolved,
        "log_sha256": hashlib.sha256(log_data).hexdigest(),
        "log_bytes": len(log_data),
        "guard_output_tail": log_data.decode("utf-8", errors="replace")[-1200:],
    }
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("instance_id")
    parser.add_argument("stage")
    parser.add_argument("patch", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = grade(args.instance_id, args.stage, args.patch, args.output)
    print(
        json.dumps(
            {k: result[k] for k in ("instance_id", "stage", "resolved", "valid_log", "exit_code")}
        )
    )


if __name__ == "__main__":
    main()
