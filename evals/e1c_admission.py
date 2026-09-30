"""Run one E1-C public-task admission probe in the official SWE-bench image.

This does not call a model or admit a cohort. Each phase starts from a fresh
container; the pinned upstream parser decides the targeted test statuses.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import time
import types
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / ".codex" / "e1c" / "tasks"
UPSTREAM = ROOT / ".codex" / "e1c" / "swebench-harness"
PARSER_COMMIT = "02e7a74ffd0b707aab73d203fe87bdc7c76afc8e"
SETUP_ONLY_PATHS = frozenset({"setup.py", "tox.ini"})


def source_identity(log_bytes: bytes, patch_paths: tuple[Path, ...]) -> dict:
    def marker(name: bytes) -> str | None:
        match = re.search(rb"E1C_" + name + rb":([0-9a-f]{40})", log_bytes)
        return match.group(1).decode("ascii") if match else None

    head = marker(b"CONTAINER_HEAD")
    expected_tree = marker(b"EXPECTED_TREE")
    actual_tree = marker(b"ACTUAL_TREE")
    image_diff_paths = [
        path.decode("utf-8", errors="replace")
        for path in re.findall(rb"^E1C_IMAGE_DIFF_PATH:([^\r\n]+)\r?$", log_bytes, re.MULTILINE)
    ]
    overlap = []
    for patch_path in patch_paths:
        patch = patch_path.read_bytes()
        for path in image_diff_paths:
            if re.search(rb"^diff --git a/" + re.escape(path.encode()) + rb" b/" + re.escape(path.encode()) + rb"\r?$", patch, re.MULTILINE):
                overlap.append(path)
    tree_match = bool(head and expected_tree and actual_tree == expected_tree)
    setup_only = (
        bool(head and expected_tree and actual_tree and image_diff_paths)
        and set(image_diff_paths) <= SETUP_ONLY_PATHS
        and not overlap
    )
    return {
        "container_head": head,
        "expected_base_tree": expected_tree,
        "actual_container_tree": actual_tree,
        "source_tree_match": tree_match,
        "image_setup_diff_paths": image_diff_paths,
        "patch_image_setup_overlap": sorted(set(overlap)),
        "source_identity_valid": tree_match or setup_only,
    }


def _official_grader():
    if (
        subprocess.check_output(
            ["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True
        ).strip()
        != PARSER_COMMIT
    ):
        raise RuntimeError("official parser checkout is not pinned")
    sys.path.insert(0, str(UPSTREAM))
    harness = types.ModuleType("swebench.harness")
    harness.__path__ = [str(UPSTREAM / "swebench" / "harness")]
    sys.modules[harness.__name__] = harness
    package = types.ModuleType("swebench.harness.log_parsers")
    package.__path__ = [str(UPSTREAM / "swebench" / "harness" / "log_parsers")]
    sys.modules[package.__name__] = package
    source = UPSTREAM / "swebench" / "harness" / "log_parsers" / "python.py"
    spec = importlib.util.spec_from_file_location(f"{package.__name__}.python", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("official parser unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    package.PARSER_REGISTRY = {
        name: getattr(module, name) for name in dir(module) if name.startswith("parse_log_")
    }
    from swebench.harness.grading import _resolve_case, get_logs_eval, test_maintained, test_passed
    from swebench.types import TestSpec

    return get_logs_eval, test_maintained, test_passed, _resolve_case, TestSpec


def probe(
    instance_id: str,
    phase: str,
    timeout: int = 1800,
    *,
    task_root: Path = TASKS,
    artifact_root: Path | None = None,
) -> dict:
    if sys.platform == "win32" and not sys.flags.utf8_mode:
        raise RuntimeError("Windows official SWE-bench log parsing requires python -X utf8")
    task_dir = task_root / instance_id
    if not task_dir.is_dir() or task_dir.name != instance_id:
        raise ValueError("unknown task directory")
    task = yaml.safe_load((task_dir / "task.yaml").read_text(encoding="utf-8"))
    tests = json.loads((task_dir / "tests.json").read_text(encoding="utf-8"))
    if (
        task["instance_id"] != instance_id
        or not isinstance(tests.get("FAIL_TO_PASS"), list)
        or not tests["FAIL_TO_PASS"]
        or not isinstance(tests.get("PASS_TO_PASS"), list)
    ):
        raise ValueError("task metadata mismatch or invalid test class")
    get_logs_eval, test_maintained, test_passed, resolve_case, TestSpec = _official_grader()
    artifact_dir = (
        artifact_root / instance_id
        if artifact_root is not None
        else ROOT / ".codex" / "e1c" / "admission_v2" / instance_id
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)
    log_path = artifact_dir / f"{phase}.log"
    result_path = artifact_dir / f"{phase}.json"
    if result_path.exists() or log_path.exists():
        raise FileExistsError("admission phase already has an artifact; no silent retry")
    expected = task["base_commit"]
    if not re.fullmatch(r"[0-9a-f]{40}", expected) or not re.fullmatch(
        r"swebench/[A-Za-z0-9_.-]+:latest", task["image"]
    ):
        raise ValueError("unsafe base commit or nonofficial image reference")
    image_digest = subprocess.check_output(
        ["docker", "image", "inspect", task["image"], "--format", "{{index .RepoDigests 0}}"],
        text=True,
    ).strip()
    if not re.fullmatch(r"swebench/[A-Za-z0-9_.-]+@sha256:[0-9a-f]{64}", image_digest):
        raise ValueError("official image digest unavailable")
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
        'while IFS= read -r file; do '
        'echo "E1C_IMAGE_DIFF_PATH:$file"; '
        'case "$file" in setup.py|tox.ini) ;; *) exit 81;; esac; '
        f'done < <(git -C /testbed diff --name-only "{expected}" HEAD); '
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
        "--name",
        f"e1c-admit-{instance_id}-{phase}",
        "--mount",
        f"type=bind,source={task_dir},target=/admission,readonly",
        task["image"],
        "bash",
        "-lc",
        script,
    ]
    started = time.monotonic()
    timed_out = False
    with log_path.open("wb") as log:
        try:
            completed = subprocess.run(
                command, stdout=log, stderr=subprocess.STDOUT, timeout=timeout, check=False
            )
            exit_code = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out, exit_code = True, None
            subprocess.run(
                ["docker", "rm", "-f", f"e1c-admit-{instance_id}-{phase}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
                check=False,
            )
    duration = round(time.monotonic() - started, 3)
    log_bytes = log_path.read_bytes()

    identity = source_identity(log_bytes, (task_dir / "gold.patch", task_dir / "test.patch"))
    source_match = identity["source_identity_valid"]
    spec = TestSpec(
        instance_id=instance_id,
        image=task["image"],
        eval_script_list=[],
        repo=task["repo"],
        version=str(task.get("version", "")),
        FAIL_TO_PASS=tests["FAIL_TO_PASS"],
        PASS_TO_PASS=tests["PASS_TO_PASS"],
        log_parser=task["log_parser"],
    )
    statuses, valid_log = get_logs_eval(spec, str(log_path)) if not timed_out else ({}, False)
    f2p_pass = [name for name in tests["FAIL_TO_PASS"] if test_passed(name, statuses)]
    p2p_maintained = [name for name in tests["PASS_TO_PASS"] if test_maintained(name, statuses)]
    f2p_explicit_fail = [
        name
        for name in tests["FAIL_TO_PASS"]
        if (key := resolve_case(name, statuses)) is not None
        and statuses[key] in {"FAILED", "ERROR"}
    ]
    if phase == "base":
        admitted_phase = source_match and valid_log and bool(f2p_explicit_fail)
    else:
        admitted_phase = (
            source_match
            and valid_log
            and exit_code == 0
            and len(f2p_pass) == len(tests["FAIL_TO_PASS"])
            and len(p2p_maintained) == len(tests["PASS_TO_PASS"])
        )
    result = {
        "schema": "e1c-admission-phase-v2",
        "instance_id": instance_id,
        "phase": phase,
        "official_parser_commit": PARSER_COMMIT,
        "image": task["image"],
        "image_digest": image_digest,
        "expected_base_commit": expected,
        **identity,
        "command": command,
        "exit_code": exit_code,
        "timeout": timed_out,
        "duration_seconds": duration,
        "log_bytes": len(log_bytes),
        "log_sha256": hashlib.sha256(log_bytes).hexdigest(),
        "valid_log": valid_log,
        "parsed_test_count": len(statuses),
        "f2p_pass": len(f2p_pass),
        "f2p_explicit_fail": len(f2p_explicit_fail),
        "f2p_total": len(tests["FAIL_TO_PASS"]),
        "p2p_maintained": len(p2p_maintained),
        "p2p_total": len(tests["PASS_TO_PASS"]),
        "phase_pass": admitted_phase,
        "log_path": str(log_path),
    }
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("instance_id")
    parser.add_argument("phase", choices=("base", "gold"))
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    print(json.dumps(probe(args.instance_id, args.phase, args.timeout), ensure_ascii=False))


if __name__ == "__main__":
    main()
