"""Manifest-gated, one-shot acquisition for frozen strict-v5 official images."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

from evals.e1c_admission import ROOT

MANIFEST = ROOT / "data" / "e1c_strict_v5_canary_manifest.json"
OUT = ROOT / "data" / "e1c_strict_v5_official_image_acquisition.json"


def _remote_manifest(image: str, timeout: int = 45) -> dict:
    try:
        completed = subprocess.run(
            ["docker", "buildx", "imagetools", "inspect", "--raw", image],
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ready": False, "digest": None, "error_tail": "official_manifest_timeout"}
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode(errors="replace").strip()
        return {
            "ready": False,
            "digest": None,
            "error_sha256": hashlib.sha256(detail.encode()).hexdigest(),
            "error_tail": detail[-500:],
        }
    try:
        payload = json.loads(completed.stdout)
    except (ValueError, TypeError):
        return {"ready": False, "digest": None, "error_tail": "invalid_official_manifest_json"}
    digest = "sha256:" + hashlib.sha256(completed.stdout).hexdigest()
    if "manifests" not in payload:
        try:
            details = subprocess.run(
                ["docker", "buildx", "imagetools", "inspect", "--format", "{{json .}}", image],
                capture_output=True,
                timeout=timeout,
                check=False,
            )
            metadata = json.loads(details.stdout) if details.returncode == 0 else {}
        except (subprocess.TimeoutExpired, ValueError):
            metadata = {}
        platform = metadata.get("image") or {}
        ready = (
            metadata.get("manifest", {}).get("digest") == digest
            and platform.get("architecture") == "amd64"
            and platform.get("os") == "linux"
        )
        return {
            "ready": ready,
            "digest": digest if ready else None,
            "platform": {"architecture": "amd64", "os": "linux"} if ready else None,
        }
    matching = [
        entry for entry in payload.get("manifests", [])
        if entry.get("platform", {}).get("architecture") == "amd64"
        and entry.get("platform", {}).get("os") == "linux"
    ]
    ready = len(matching) == 1 and matching[0].get("digest", "").startswith("sha256:")
    return {
        "ready": ready,
        "digest": digest if ready else None,
        "platform": {"architecture": "amd64", "os": "linux"} if ready else None,
        "platform_digest": matching[0]["digest"] if ready else None,
    }


def _local_repo_digest(image: str) -> str | None:
    completed = subprocess.run(
        ["docker", "image", "inspect", image, "--format", "{{index .RepoDigests 0}}"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value or None


def _digest_part(repo_digest: str | None) -> str | None:
    if not repo_digest or "@sha256:" not in repo_digest:
        return None
    return repo_digest.split("@", 1)[1]


def acquire(pull_timeout: int = 900, output: Path = OUT) -> dict:
    frozen = json.loads(MANIFEST.read_text(encoding="utf-8"))
    preflight = []
    for task in frozen["tasks"]:
        remote = _remote_manifest(task["image"])
        preflight.append(
            {
                "instance_id": task["instance_id"],
                "image": task["image"],
                "remote": remote,
            }
        )
    if not all(row["remote"]["ready"] for row in preflight):
        result = {
            "schema": "e1c-strict-v5-official-image-acquisition-v1",
            "ready": False,
            "reason": "official_manifest_preflight_incomplete",
            "pull_attempted": False,
            "rows": preflight,
            "provider_calls": 0,
            "live_model_run": False,
        }
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result

    rows = []
    for row in preflight:
        image = row["image"]
        remote_digest = row["remote"]["digest"]
        local_before = _local_repo_digest(image)
        attempted = local_before is None or _digest_part(local_before) != remote_digest
        exit_code = 0
        timed_out = False
        started = time.monotonic()
        if attempted:
            try:
                completed = subprocess.run(
                    ["docker", "pull", "--platform", "linux/amd64", image],
                    capture_output=True,
                    text=True,
                    timeout=pull_timeout,
                    check=False,
                )
                exit_code = completed.returncode
            except subprocess.TimeoutExpired:
                timed_out, exit_code = True, -1
        local_after = _local_repo_digest(image)
        local_digest = _digest_part(local_after)
        rows.append(
            {
                **row,
                "pull_attempted": attempted,
                "pull_exit_code": exit_code,
                "pull_timeout": timed_out,
                "local_repo_digest": local_after,
                "digest_match": local_digest == remote_digest,
                "duration_seconds": round(time.monotonic() - started, 3),
            }
        )
        if timed_out or exit_code != 0 or local_digest != remote_digest:
            break

    complete = (
        len(rows) == len(preflight)
        and all(row["digest_match"] and row["pull_exit_code"] == 0 for row in rows)
    )
    result = {
        "schema": "e1c-strict-v5-official-image-acquisition-v1",
        "ready": complete,
        "reason": "official_images_digest_verified" if complete else "official_image_acquisition_incomplete",
        "pull_attempted": any(row["pull_attempted"] for row in rows),
        "rows": rows,
        "provider_calls": 0,
        "live_model_run": False,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pull-timeout", type=int, default=900)
    args = parser.parse_args()
    print(json.dumps(acquire(pull_timeout=args.pull_timeout), indent=2))
