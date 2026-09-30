"""Zero-model, grader-only Base/Gold pilot for frozen evaluation_2 DEV12.

The official test files and logs stay under ``.codex/e1c/evaluation_2/grader-only``;
none of them are inputs to issue-only localization or probe generation.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import time
import urllib.request
from pathlib import Path

import yaml

from evals.e1c_admission import _official_grader
from evals.e1c_evaluation_2 import IDENTITY, ROOT
from evals.e1c_evaluation_2_metadata import OUT as METADATA
from evals.e1c_evaluation_2_probe import SOURCE_IDENTITY_SHELL, verified_local_image

OUT = ROOT / ".codex/e1c/evaluation_2/grader-only"
FILES = ("task.yaml", "tests.json", "gold.patch", "test.patch", "eval.sh")
TREE = OUT / "frozen-task-blobs.json"


def _official_file(revision: str, path: str, expected_blob: str) -> bytes:
    """Fetch a frozen official blob through GitHub Contents when raw hosting is unavailable."""
    url = f"https://api.github.com/repos/SWE-bench/swe-bench-tasks/contents/{path}?ref={revision}"
    request = urllib.request.Request(url, headers={"User-Agent": "e1c-evaluation-2-grader-only"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("path") != path or payload.get("sha") != expected_blob or payload.get("encoding") != "base64":
        raise ValueError("official grader Contents metadata differs from frozen tree")
    return base64.b64decode(payload["content"])


def _task(instance_id: str) -> tuple[dict, str]:
    identity = json.loads(IDENTITY.read_bytes())
    metadata = json.loads(METADATA.read_bytes())
    if identity["source_revision"] != metadata["source_revision"]:
        raise ValueError("DEV12 metadata revision changed")
    if instance_id not in {row["instance_id"] for row in identity["tasks"]}:
        raise ValueError("task is not in frozen DEV12")
    rows = [row for row in metadata["tasks"] if row["instance_id"] == instance_id]
    if len(rows) != 1:
        raise ValueError("DEV12 task metadata missing or duplicated")
    return rows[0], identity["source_revision"]


def _blobs(revision: str) -> dict[str, str]:
    if TREE.is_file():
        value = json.loads(TREE.read_text(encoding="utf-8"))
    else:
        request = urllib.request.Request(
            f"https://api.github.com/repos/SWE-bench/swe-bench-tasks/git/trees/{revision}?recursive=1",
            headers={"User-Agent": "e1c-evaluation-2-grader-only"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
        if payload.get("truncated"):
            raise ValueError("official task tree was truncated")
        prefixes = {f"tasks/{row['instance_id']}/" for row in json.loads(METADATA.read_bytes())["tasks"]}
        value = {
            "source_revision": revision,
            "sha": {
                item["path"]: item["sha"] for item in payload["tree"]
                if item["type"] == "blob" and any(item["path"].startswith(prefix) for prefix in prefixes)
            },
        }
        TREE.parent.mkdir(parents=True, exist_ok=True)
        TREE.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    if value["source_revision"] != revision:
        raise ValueError("grader task tree revision differs from frozen DEV12")
    for row in json.loads(METADATA.read_bytes())["tasks"]:
        if value["sha"].get(f"tasks/{row['instance_id']}/task.yaml") != row["_provenance"]["task_yaml_blob_sha"]:
            raise ValueError("official task tree differs from frozen DEV12 metadata")
    return value["sha"]


def materialize(instance_id: str) -> Path:
    task, revision = _task(instance_id)
    blobs = _blobs(revision)
    destination = OUT / instance_id
    destination.mkdir(parents=True, exist_ok=True)
    record_path = destination / "materialization.json"
    previous = json.loads(record_path.read_text(encoding="utf-8")) if record_path.is_file() else None
    if previous is not None and (
        previous.get("instance_id") != instance_id or previous.get("source_revision") != revision
    ):
        raise ValueError("existing grader materialization is not frozen DEV12")
    hashes: dict[str, str] = {}
    for name in FILES:
        target = destination / name
        expected_blob = blobs.get(f"tasks/{instance_id}/{name}")
        if not expected_blob:
            raise ValueError("required grader file absent from frozen official task tree")
        raw = target.read_bytes() if target.is_file() else None
        if raw is None:
            raw = _official_file(revision, f"tasks/{instance_id}/{name}", expected_blob)
            with target.open("xb") as handle:
                handle.write(raw)
        blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        if blob != expected_blob:
            raise ValueError("grader file differs from frozen official task tree")
        if raw is None or (previous is not None and previous["sha256"].get(name) != hashlib.sha256(raw).hexdigest()):
            raise ValueError("grader-only file differs from frozen materialization")
        hashes[name] = hashlib.sha256(raw).hexdigest()
    task_yaml = yaml.safe_load((destination / "task.yaml").read_text(encoding="utf-8"))
    if any(task_yaml.get(key) != task[key] for key in ("instance_id", "repo", "base_commit", "image")):
        raise ValueError("grader task.yaml does not match frozen DEV12 metadata")
    record = {
        "schema": "e1c-evaluation-2-grader-materialization-v1",
        "instance_id": instance_id,
        "source_revision": revision,
        "grader_only": True,
        "provider_calls": 0,
        "sha256": hashes,
    }
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return destination


def run_phase(instance_id: str, phase: str, *, timeout: int = 900) -> dict:
    if phase not in {"base", "gold"} or timeout < 1:
        raise ValueError("phase must be base or gold with a positive timeout")
    task, _ = _task(instance_id)
    grader = materialize(instance_id)
    image = verified_local_image(instance_id)
    actual_image = subprocess.check_output(
        ["docker", "image", "inspect", image, "--format", "{{.Id}}"], text=True, timeout=30
    ).strip()
    if actual_image != image:
        raise ValueError("frozen local image ID is unavailable")
    log_path = grader / f"{phase}.log"
    result_path = grader / f"{phase}.json"
    if log_path.exists() or result_path.exists():
        raise FileExistsError("admission phase has an artifact; no silent retry")
    script = (
        SOURCE_IDENTITY_SHELL
        + 'echo "E1C2_SOURCE_IDENTITY:PASS"; cd /testbed; '
        + ('git apply --check /admission/gold.patch && git apply /admission/gold.patch || exit 91; ' if phase == "gold" else "")
        + "bash /admission/eval.sh"
    )
    name = f"e1c2-admit-{instance_id}-{phase}"
    command = [
        "docker", "run", "--rm", "--pull=never", "--platform", "linux/amd64", "--network", "none",
        "--pids-limit", "512", "--memory", "6g", "--cpus", "2", "--name", name,
        "--env", "GIT_CONFIG_COUNT=1", "--env", "GIT_CONFIG_KEY_0=safe.directory",
        "--env", "GIT_CONFIG_VALUE_0=/testbed",
        "--mount", f"type=bind,source={grader.resolve()},target=/admission,readonly",
        image, "sh", "-c", script, "e1c2", task["base_commit"],
    ]
    started = time.monotonic()
    timed_out = False
    with log_path.open("xb") as log:
        try:
            completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=timeout, check=False)
            returncode = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out, returncode = True, None
            subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=30, check=False)
    get_logs_eval, test_maintained, test_passed, resolve_case, TestSpec = _official_grader()
    tests = json.loads((grader / "tests.json").read_text(encoding="utf-8"))
    task_yaml = yaml.safe_load((grader / "task.yaml").read_text(encoding="utf-8"))
    spec = TestSpec(
        instance_id=instance_id, image=task["image"], eval_script_list=[], repo=task["repo"],
        version=str(task_yaml.get("version", "")), FAIL_TO_PASS=tests["FAIL_TO_PASS"],
        PASS_TO_PASS=tests["PASS_TO_PASS"], log_parser=task_yaml["log_parser"],
    )
    statuses, valid_log = get_logs_eval(spec, str(log_path)) if not timed_out else ({}, False)
    f2p_fail = sum(
        (key := resolve_case(case, statuses)) is not None and statuses[key] in {"FAILED", "ERROR"}
        for case in tests["FAIL_TO_PASS"]
    )
    f2p_pass = sum(test_passed(case, statuses) for case in tests["FAIL_TO_PASS"])
    p2p_maintained = sum(test_maintained(case, statuses) for case in tests["PASS_TO_PASS"])
    source_ok = b"E1C2_SOURCE_IDENTITY:PASS" in log_path.read_bytes()
    passed = bool(source_ok and valid_log and (
        f2p_fail > 0 if phase == "base" else
        returncode == 0 and f2p_pass == len(tests["FAIL_TO_PASS"]) and p2p_maintained == len(tests["PASS_TO_PASS"])
    ))
    result = {
        "schema": "e1c-evaluation-2-official-admission-phase-v1",
        "instance_id": instance_id, "phase": phase, "phase_pass": passed,
        "image_id": image, "source_identity_pass": source_ok,
        "valid_official_log": valid_log, "returncode": returncode, "timed_out": timed_out,
        "f2p_total": len(tests["FAIL_TO_PASS"]), "f2p_explicit_fail": f2p_fail, "f2p_pass": f2p_pass,
        "p2p_total": len(tests["PASS_TO_PASS"]), "p2p_maintained": p2p_maintained,
        "log_sha256": hashlib.sha256(log_path.read_bytes()).hexdigest(),
        "duration_seconds": round(time.monotonic() - started, 2),
        "grader_only": True, "repair_visible": False, "provider_calls": 0,
    }
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instance_id")
    parser.add_argument("phase", choices=("base", "gold"))
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    print(json.dumps(run_phase(args.instance_id, args.phase, timeout=args.timeout), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
