"""Canonical testbed-interpreter executor for strict E1-C successor development."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path

from evals.e1c_strict_successor_expected_failure import (
    CompiledScenario,
    classify_failure,
    render_compiled,
)

CANONICAL_TESTBED_PYTHON = "/opt/miniconda3/envs/testbed/bin/python"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def probe_canonical_interpreter(image_digest: str, *, timeout_seconds: int = 30) -> dict:
    command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        image_digest,
        "sh",
        "-lc",
        f"test -x {CANONICAL_TESTBED_PYTHON} && {CANONICAL_TESTBED_PYTHON} -V",
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
    )
    return {
        "image_digest": image_digest,
        "network_disabled": True,
        "canonical_python": CANONICAL_TESTBED_PYTHON,
        "available": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout_sha256": _sha(completed.stdout),
        "stderr_sha256": _sha(completed.stderr),
        "version_text": (completed.stdout or completed.stderr).strip(),
    }


def run_cti_preflight(
    compiled: CompiledScenario,
    *,
    source_root: Path,
    expected_base_commit: str,
    image_digest: str,
    artifact_path: Path,
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
    rendered = render_compiled(compiled)
    command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--workdir",
        "/testbed",
        image_digest,
        CANONICAL_TESTBED_PYTHON,
        "-X",
        "utf8",
        "-c",
        rendered,
    ]
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

    matched, reason, observed = classify_failure(compiled.contract, stderr, returncode)
    exact_base = bool(expected_base_commit) and expected_base_commit == observed_base_commit
    immutable_image = "@sha256:" in image_digest
    network_disabled = "--network" in command and command[command.index("--network") + 1] == "none"
    trusted = all((not timed_out, exact_base, immutable_image, network_disabled, matched))
    value = {
        "schema": "e1c-strict-successor-cti-preflight-v1",
        "provider_calls": 0,
        "candidate_path": compiled.candidate_path,
        "canonical_python": CANONICAL_TESTBED_PYTHON,
        "compiled_body_sha256": _sha(compiled.body_source),
        "binding_count": len(compiled.bindings),
        "bindings": [asdict(binding) for binding in compiled.bindings],
        "expected_contract": asdict(compiled.contract),
        "observed_contract": asdict(observed) if observed else None,
        "expected_base_commit": expected_base_commit,
        "observed_base_commit": observed_base_commit,
        "image_digest": image_digest,
        "exact_base_identity": exact_base,
        "immutable_image_identity": immutable_image,
        "network_disabled": network_disabled,
        "executed": returncode is not None and not timed_out,
        "timed_out": timed_out,
        "returncode": returncode,
        "stdout_sha256": _sha(stdout),
        "stderr_sha256": _sha(stderr),
        "trusted_reproducer": trusted,
        "classification": reason if not trusted else "trusted_expected_failure_reproduced",
        "timeout_seconds": timeout_seconds,
    }
    value["preflight_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(payload, encoding="utf-8")
    value["artifact_file_sha256"] = _sha(payload)
    return value
