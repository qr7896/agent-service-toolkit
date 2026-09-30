"""Bounded executor for strict-successor scenario preflights."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from evals.e1c_strict_successor_scenario_preflight import assess, persist
from evals.e1c_strict_v7_runner import docker_command


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def run_preflight(
    witness: dict,
    *,
    source_root: Path,
    expected_base_commit: str,
    image_digest: str,
    artifact_path: Path,
    import_map: dict[str, str] | None = None,
    timeout_seconds: int = 60,
) -> dict:
    if timeout_seconds < 1 or timeout_seconds > 120:
        raise ValueError("preflight timeout must be within 1..120 seconds")
    head = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    observed_base_commit = head.stdout.strip() if head.returncode == 0 else ""
    command = docker_command(witness, image_digest, import_map=import_map or {})
    timed_out = False
    returncode = None
    stdout = ""
    stderr = ""
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    value = assess(
        witness,
        expected_base_commit=expected_base_commit,
        observed_base_commit=observed_base_commit,
        image_digest=image_digest,
        command=command,
        returncode=returncode,
        timed_out=timed_out,
        stdout_sha256=_hash(stdout),
        stderr_sha256=_hash(stderr),
    )
    value["timeout_seconds"] = timeout_seconds
    value["artifact_file_sha256"] = persist(value, artifact_path)
    return value
