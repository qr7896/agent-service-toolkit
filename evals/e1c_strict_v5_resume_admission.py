"""Resume strict-v5 zero-provider admission only when frozen official images exist."""

from __future__ import annotations

import json
import subprocess

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_admission_report import build as build_admission
from evals.e1c_strict_v5_admission_seal import build as build_seal
from evals.e1c_strict_v5_verification import run as run_verification

MANIFEST = ROOT / "data" / "e1c_strict_v5_canary_manifest.json"


def _local_digest(image: str) -> str | None:
    completed = subprocess.run(
        ["docker", "image", "inspect", image, "--format", "{{index .RepoDigests 0}}"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def inspect_local_images() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    image_rows = [
        {
            "instance_id": task["instance_id"],
            "image": task["image"],
            "digest": _local_digest(task["image"]),
        }
        for task in manifest["tasks"]
    ]
    missing = [row["instance_id"] for row in image_rows if row["digest"] is None]
    return {
        "ready": not missing,
        "missing_instance_ids": missing,
        "image_rows": image_rows,
    }


def run() -> dict:
    local = inspect_local_images()
    image_rows = local["image_rows"]
    missing = local["missing_instance_ids"]
    if missing:
        return {
            "schema": "e1c-strict-v5-resume-admission-v1",
            "ready": False,
            "reason": "frozen_official_images_missing",
            "missing_instance_ids": missing,
            "image_rows": image_rows,
            "provider_calls": 0,
            "live_model_run": False,
        }
    verification = run_verification()
    admission = build_admission()
    seal = build_seal()
    return {
        "schema": "e1c-strict-v5-resume-admission-v1",
        "ready": bool(seal.get("live_allowed")),
        "reason": seal.get("reason"),
        "image_rows": image_rows,
        "verification_ready": verification.get("ready"),
        "admission_ready": admission.get("ready"),
        "seal_live_allowed": seal.get("live_allowed"),
        "provider_calls": 0,
        "live_model_run": False,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
