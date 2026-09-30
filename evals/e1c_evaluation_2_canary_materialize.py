"""Materialize frozen canary public issue and exact-base source; keep grader files isolated."""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import urllib.request

from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_canary_acquire import OUT as ACQUIRE
from evals.e1c_evaluation_2_canary_metadata import OUT as METADATA
from evals.e1c_evaluation_2_canary_select import IDENTITY
from evals.e1c_evaluation_2_canary_transport import OUT as TRANSPORT
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_probe import freeze_input
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

OUT = ROOT / ".codex/e1c/evaluation_2/canary-v1"
PUBLIC = OUT / "issue-only"
SOURCE = OUT / "source"
GRADER = OUT / "grader-only"


def rows() -> list[dict]:
    identity = json.loads(IDENTITY.read_bytes())
    metadata = json.loads(METADATA.read_bytes())
    if metadata.get("identity_sha256") != _sha(IDENTITY) or len(metadata.get("tasks", [])) != 3:
        raise ValueError("canary official metadata identity changed")
    if [task["instance_id"] for task in identity["tasks"]] != [task["instance_id"] for task in metadata["tasks"]]:
        raise ValueError("canary task order changed")
    return metadata["tasks"]


def verified_image(instance_id: str) -> str:
    transport = json.loads(TRANSPORT.read_bytes())
    if transport.get("identity_sha256") != _sha(IDENTITY) or transport.get("metadata_sha256") != _sha(METADATA):
        raise ValueError("canary transport identity changed")
    match = [row for row in transport["rows"] if row["instance_id"] == instance_id]
    if len(match) != 1 or match[0].get("digest_identical") is not True:
        raise ValueError("canary official/mirror digest not established")
    status = json.loads((ACQUIRE / instance_id / "loaded.json").read_bytes())
    image = status.get("config_digest")
    if (
        status.get("transport_sha256") != _sha(TRANSPORT)
        or status.get("top_digest") != match[0]["official"]["top_digest"]
        or status.get("platform_digest") != match[0]["official"]["platform_digest"]
        or status.get("load", {}).get("loaded_config_digest") != image
        or not isinstance(image, str)
        or not image.startswith("sha256:")
    ):
        raise ValueError("canary local image is not official-digest bound")
    inspected = subprocess.run(["docker", "image", "inspect", image, "--format", "{{.Id}}"], capture_output=True, text=True, timeout=30, check=False)
    if inspected.returncode or inspected.stdout.strip() != image:
        raise ValueError("canary Docker image unavailable or changed")
    return image


def official_blob(instance_id: str, name: str) -> tuple[bytes, str]:
    if name not in {"problem_statement.md", "task.yaml", "tests.json", "gold.patch", "test.patch", "eval.sh"}:
        raise ValueError("unapproved official task file")
    identity = json.loads(IDENTITY.read_bytes())
    if instance_id not in {row["instance_id"] for row in identity["tasks"]}:
        raise ValueError("task outside fixed canary")
    path = f"tasks/{instance_id}/{name}"
    url = f"https://api.github.com/repos/SWE-bench/swe-bench-tasks/contents/{path}?ref={identity['source_revision']}"
    request = urllib.request.Request(url, headers={"User-Agent": "e1c2-independent-canary"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    raw = base64.b64decode(payload["content"])
    digest = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
    if digest != payload["sha"] or payload["path"] != path:
        raise ValueError("official task file blob mismatch")
    if name == "task.yaml":
        metadata = next(row for row in rows() if row["instance_id"] == instance_id)
        if digest != metadata["_provenance"]["task_yaml_blob_sha"]:
            raise ValueError("official task.yaml differs from selected metadata")
    return raw, digest


def materialize_public(instance_id: str) -> dict:
    task = next(row for row in rows() if row["instance_id"] == instance_id)
    image = verified_image(instance_id)
    destination = SOURCE / instance_id
    if not destination.is_dir():
        destination.mkdir(parents=True)
        name = "e1c2-canary-source-" + hashlib.sha256(instance_id.encode()).hexdigest()[:16]
        subprocess.run(["docker", "create", "--name", name, "--pull", "never", image], capture_output=True, timeout=30, check=True)
        try:
            subprocess.run(["docker", "cp", f"{name}:/testbed/.", str(destination)], capture_output=True, timeout=300, check=True)
        finally:
            subprocess.run(["docker", "rm", name], capture_output=True, timeout=30, check=False)
        subprocess.run(["git", "-C", str(destination), "config", "core.filemode", "false"], check=True)
        subprocess.run(["git", "-C", str(destination), "checkout", "--detach", task["base_commit"]], capture_output=True, timeout=90, check=True)
    head = subprocess.check_output(["git", "-C", str(destination), "rev-parse", "HEAD"], text=True, timeout=30).strip()
    status = subprocess.check_output(["git", "-C", str(destination), "status", "--porcelain", "--untracked-files=all"], text=True, timeout=90).strip()
    if head != task["base_commit"] or status:
        raise ValueError("canary production source not clean at exact base")
    issue_path = PUBLIC / instance_id / "problem_statement.md"
    issue_path.parent.mkdir(parents=True, exist_ok=True)
    if issue_path.is_file():
        raw = issue_path.read_bytes()
        _, blob = official_blob(instance_id, "problem_statement.md")
        if hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest() != blob:
            raise ValueError("saved public issue changed")
    else:
        raw, blob = official_blob(instance_id, "problem_statement.md")
        with issue_path.open("xb") as handle:
            handle.write(raw)
    frozen = freeze_input(raw.decode("utf-8"), destination, task["base_commit"], balanced=True)
    frozen.pop("input_sha256")
    frozen["schema"] = "e1c-evaluation-2-probe-input-v4"
    frozen["input_sha256"] = audit_repair_visible_payload(frozen)
    input_path = PUBLIC / instance_id / "frozen_input_v4.json"
    if input_path.is_file():
        if json.loads(input_path.read_bytes()) != frozen:
            raise ValueError("canary issue-only input changed")
    else:
        _save(input_path, frozen)
    return {"instance_id": instance_id, "image_id": image, "issue_blob_sha": blob, "input_sha256": _sha(input_path), "source_head": head, "candidate_count": frozen["candidate_count"], "provider_calls": 0}


if __name__ == "__main__":
    for task_row in rows():
        iid = task_row["instance_id"]
        admissions = [GRADER / iid / f"{phase}.json" for phase in ("base", "gold")]
        if not all(path.is_file() and json.loads(path.read_bytes()).get("phase_pass") is True for path in admissions):
            print(json.dumps({"instance_id": iid, "status": "fixed_denominator_official_admission_failed", "provider_calls": 0}), flush=True)
            continue
        print(json.dumps(materialize_public(iid), ensure_ascii=False), flush=True)
