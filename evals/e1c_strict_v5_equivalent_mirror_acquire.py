"""Acquire frozen images through a digest-proven equivalent mirror."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from evals.e1c_admission import ROOT

OUT = ROOT / "data" / "e1c_strict_v5_equivalent_mirror_acquisition.json"


def _repo_digest(image: str) -> str | None:
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


def _digest_part(value: str | None) -> str | None:
    if not value or "@sha256:" not in value:
        return None
    return value.split("@", 1)[1]


def acquire(identity: dict, pull_timeout: int = 900, output: Path = OUT) -> dict:
    if not identity.get("mirror_transport_ready"):
        result = {
            "schema": "e1c-strict-v5-equivalent-mirror-acquisition-v1",
            "ready": False,
            "reason": "mirror_transport_not_digest_proven",
            "pull_attempted": False,
            "provider_calls": 0,
            "live_model_run": False,
            "rows": [],
        }
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result

    rows = []
    for source in identity["rows"]:
        expected = source["authoritative_digest"]
        mirror = source["mirror_image"]
        official = source["official_image"]
        local_before = _repo_digest(mirror)
        attempted = _digest_part(local_before) != expected
        exit_code = 0
        timed_out = False
        started = time.monotonic()
        if attempted:
            try:
                completed = subprocess.run(
                    ["docker", "pull", "--platform", "linux/amd64", mirror],
                    capture_output=True,
                    text=True,
                    timeout=pull_timeout,
                    check=False,
                )
                exit_code = completed.returncode
            except subprocess.TimeoutExpired:
                timed_out, exit_code = True, -1
        mirror_after = _repo_digest(mirror)
        mirror_match = _digest_part(mirror_after) == expected
        tag_exit_code = None
        official_after = None
        official_match = False
        if not timed_out and exit_code == 0 and mirror_match:
            tagged = subprocess.run(
                ["docker", "tag", mirror, official],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            tag_exit_code = tagged.returncode
            if tagged.returncode == 0:
                official_after = _repo_digest(official)
                official_match = _digest_part(official_after) == expected
        row = {
            "instance_id": source["instance_id"],
            "official_image": official,
            "mirror_image": mirror,
            "authoritative_digest": expected,
            "pull_attempted": attempted,
            "pull_exit_code": exit_code,
            "pull_timeout": timed_out,
            "mirror_repo_digest": mirror_after,
            "mirror_digest_match": mirror_match,
            "tag_exit_code": tag_exit_code,
            "official_repo_digest": official_after,
            "official_digest_match": official_match,
            "duration_seconds": round(time.monotonic() - started, 3),
        }
        rows.append(row)
        if not (
            not timed_out
            and exit_code == 0
            and mirror_match
            and tag_exit_code == 0
            and official_match
        ):
            break

    complete = (
        len(rows) == len(identity["rows"])
        and all(row["official_digest_match"] for row in rows)
    )
    result = {
        "schema": "e1c-strict-v5-equivalent-mirror-acquisition-v1",
        "ready": complete,
        "reason": (
            "equivalent_mirror_images_digest_verified"
            if complete
            else "equivalent_mirror_acquisition_incomplete"
        ),
        "pull_attempted": any(row["pull_attempted"] for row in rows),
        "provider_calls": 0,
        "live_model_run": False,
        "rows": rows,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
