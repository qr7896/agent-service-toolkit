"""Materialize only public issue prose and freeze production-only DEV12 inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import urllib.request

from evals.e1c_evaluation_2 import IDENTITY, ROOT
from evals.e1c_evaluation_2_metadata import OUT as METADATA
from evals.e1c_evaluation_2_probe import freeze_input, verified_local_image

TREE = ROOT / ".codex/e1c/evaluation_2/grader-only/frozen-task-blobs.json"
OUT = ROOT / ".codex/e1c/evaluation_2/issue-only"
SOURCE = ROOT / ".codex/e1c/evaluation_2/source"


def materialize_source(instance_id: str) -> None:
    identity = json.loads(IDENTITY.read_bytes())
    if instance_id not in {row["instance_id"] for row in identity["tasks"]}:
        raise ValueError("task is not frozen DEV12")
    task = next(row for row in json.loads(METADATA.read_bytes())["tasks"] if row["instance_id"] == instance_id)
    destination = SOURCE / instance_id
    if not destination.exists():
        destination.mkdir(parents=True)
        container = "e1c2-source-" + hashlib.sha256(instance_id.encode()).hexdigest()[:16]
        subprocess.run(
            ["docker", "create", "--name", container, "--pull", "never", verified_local_image(instance_id)],
            check=True, capture_output=True, timeout=30,
        )
        try:
            subprocess.run(
                ["docker", "cp", f"{container}:/testbed/.", str(destination)],
                check=True, capture_output=True, timeout=180,
            )
        finally:
            subprocess.run(["docker", "rm", container], capture_output=True, timeout=30, check=False)
        subprocess.run(["git", "-C", str(destination), "config", "core.filemode", "false"], check=True)
        subprocess.run(
            ["git", "-C", str(destination), "checkout", "--detach", task["base_commit"]],
            check=True, capture_output=True, timeout=60,
        )
    head = subprocess.check_output(["git", "-C", str(destination), "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output(
        ["git", "-C", str(destination), "status", "--porcelain", "--untracked-files=all"], text=True
    ).strip()
    if head != task["base_commit"] or status:
        raise ValueError("local production source is not clean at frozen base")


def freeze_task(instance_id: str, *, balanced: bool = False) -> dict:
    identity = json.loads(IDENTITY.read_bytes())
    metadata = json.loads(METADATA.read_bytes())
    if instance_id not in {row["instance_id"] for row in identity["tasks"]}:
        raise ValueError("task is not frozen DEV12")
    task = next(row for row in metadata["tasks"] if row["instance_id"] == instance_id)
    tree = json.loads(TREE.read_text(encoding="utf-8"))
    if tree["source_revision"] != identity["source_revision"]:
        raise ValueError("public issue source revision differs from frozen DEV12")
    path = f"tasks/{instance_id}/problem_statement.md"
    expected_blob = tree["sha"].get(path)
    if not expected_blob:
        raise ValueError("public issue absent from frozen official task tree")
    destination = OUT / instance_id
    destination.mkdir(parents=True, exist_ok=True)
    issue_path = destination / "problem_statement.md"
    if issue_path.is_file():
        raw = issue_path.read_bytes()
    else:
        url = f"https://raw.githubusercontent.com/SWE-bench/swe-bench-tasks/{identity['source_revision']}/{path}"
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "e1c2-issue-only"}), timeout=30) as response:
            raw = response.read()
        with issue_path.open("xb") as handle:
            handle.write(raw)
    blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
    if blob != expected_blob:
        raise ValueError("public issue differs from frozen official task tree")
    frozen = freeze_input(raw.decode("utf-8"), SOURCE / instance_id, task["base_commit"], balanced=balanced)
    output = destination / ("frozen_input_v3.json" if balanced else "frozen_input_v2.json")
    if output.is_file() and json.loads(output.read_text(encoding="utf-8")) != frozen:
        raise ValueError("existing frozen issue input changed; no silent overwrite")
    if not output.is_file():
        with output.open("x", encoding="utf-8") as handle:
            json.dump(frozen, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    return {
        "instance_id": instance_id, "status": frozen["status"],
        "candidate_count": frozen["candidate_count"], "candidate_paths": frozen["candidate_paths"],
        "input_sha256": frozen["input_sha256"], "provider_calls": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instance_id")
    parser.add_argument("--materialize-source", action="store_true")
    parser.add_argument("--balanced", action="store_true", help="freeze a new v3 input without modifying v2")
    args = parser.parse_args()
    if args.materialize_source:
        materialize_source(args.instance_id)
    print(json.dumps(freeze_task(args.instance_id, balanced=args.balanced), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
