"""Run isolated strict-v5 Base-Fail and Gold-Pass admission verification."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from evals import e1c_admission
from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_freeze_certificate import certify

MANIFEST = ROOT / "data" / "e1c_strict_v5_canary_manifest.json"
GRADER_ROOT = ROOT / ".codex" / "e1c" / "strict-v5" / "grader-only-v1"
MATERIALIZED_ROOT = ROOT / ".codex" / "e1c" / "strict-v5" / "materialized-v1"
STAGING_ROOT = ROOT / ".codex" / "e1c" / "strict-v5" / "grading-input-v1"
ARTIFACT_ROOT = ROOT / ".codex" / "e1c" / "strict-v5" / "admission-v1"
FILES = ("tests.json", "gold.patch", "test.patch", "eval.sh", "Dockerfile")


def _json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _image_digest(image: str) -> str | None:
    completed = subprocess.run(
        ["docker", "image", "inspect", image, "--format", "{{index .RepoDigests 0}}"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        return None
    digest = completed.stdout.strip()
    return digest or None


def _stage(instance_id: str) -> Path:
    source = MATERIALIZED_ROOT / instance_id / "task.yaml"
    grader = GRADER_ROOT / instance_id
    if not source.is_file() or not grader.is_dir():
        raise FileNotFoundError(instance_id)
    destination = STAGING_ROOT / instance_id
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination / "task.yaml")
    for name in FILES:
        candidate = grader / name
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        shutil.copy2(candidate, destination / name)
    return destination


def _phase(instance_id: str, phase: str, timeout: int) -> dict:
    result_path = ARTIFACT_ROOT / instance_id / f"{phase}.json"
    log_path = ARTIFACT_ROOT / instance_id / f"{phase}.log"
    existing = _json(result_path)
    if existing is not None:
        return existing
    if log_path.exists():
        return {
            "phase": phase,
            "phase_pass": False,
            "timeout": False,
            "infrastructure_failure": True,
            "status": "partial_artifact_no_retry",
        }
    return e1c_admission.probe(
        instance_id,
        phase,
        timeout=timeout,
        task_root=STAGING_ROOT,
        artifact_root=ARTIFACT_ROOT,
    )


def verify_task(instance_id: str, image: str, timeout: int = 1800) -> dict:
    _stage(instance_id)
    digest = _image_digest(image)
    if digest is None:
        value = {
            "schema": "e1c-strict-v5-verification-v1",
            "instance_id": instance_id,
            "status": "official_image_unavailable",
            "base_fail": False,
            "gold_pass": False,
            "infrastructure_failure": True,
            "image_digest": None,
            "repair_visible": False,
            "provider_calls": 0,
        }
    else:
        base = _phase(instance_id, "base", timeout)
        gold = _phase(instance_id, "gold", timeout)
        value = {
            "schema": "e1c-strict-v5-verification-v1",
            "instance_id": instance_id,
            "status": (
                "base_fail_and_gold_pass"
                if base.get("phase_pass") is True and gold.get("phase_pass") is True
                else "verification_failed"
            ),
            "base_fail": base.get("phase_pass") is True,
            "gold_pass": gold.get("phase_pass") is True,
            "infrastructure_failure": bool(
                base.get("infrastructure_failure")
                or gold.get("infrastructure_failure")
                or base.get("timeout")
                or gold.get("timeout")
            ),
            "image_digest": digest,
            "base_result_sha256": hashlib.sha256(
                json.dumps(base, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "gold_result_sha256": hashlib.sha256(
                json.dumps(gold, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "repair_visible": False,
            "provider_calls": 0,
        }
    output = MATERIALIZED_ROOT / instance_id / "verification.json"
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


def run(timeout: int = 1800) -> dict:
    certificate = certify(output=None)
    if not certificate["ready"]:
        return {
            "schema": "e1c-strict-v5-verification-summary-v1",
            "ready": False,
            "reason": "identity_freeze_not_certified",
            "provider_calls": 0,
            "rows": [],
        }
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = [
        verify_task(row["instance_id"], row["image"], timeout=timeout)
        for row in manifest["tasks"]
    ]
    return {
        "schema": "e1c-strict-v5-verification-summary-v1",
        "ready": all(
            row["base_fail"] and row["gold_pass"] and not row["infrastructure_failure"]
            for row in rows
        ),
        "reason": (
            "base_fail_gold_pass_complete"
            if all(
                row["base_fail"] and row["gold_pass"] and not row["infrastructure_failure"]
                for row in rows
            )
            else "verification_incomplete"
        ),
        "provider_calls": 0,
        "repair_visible": False,
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
