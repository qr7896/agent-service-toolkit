"""Fail closed on Docker transport failures; these are never software bug evidence."""

from __future__ import annotations

import json
import subprocess


class ContainerInfrastructureUnavailable(RuntimeError):
    pass


TRANSPORT_ERRORS = ("failed to connect to the docker api", "cannot connect to the docker daemon", "error during connect", "dockerdesktoplinuxengine")


def is_transport_failure(execution):
    return any(row.get("returncode") in {125, 126, 127}
               or any(marker in str(row.get("log_tail", "")).lower() for marker in TRANSPORT_ERRORS)
               for row in execution.get("runs", []))


def require_engine(images=()):
    try:
        result = subprocess.run(["docker", "version", "--format", "{{.Server.Version}}"], capture_output=True, text=True, timeout=20, check=False)
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise ContainerInfrastructureUnavailable("Docker engine health probe failed or timed out") from exc
    if result.returncode or not result.stdout.strip():
        raise ContainerInfrastructureUnavailable("Docker Linux Engine unavailable; no provider/candidate validation allowed")
    if images:
        try:
            result = subprocess.run(["docker", "image", "inspect", *images, "--format", "{{.Id}}"], capture_output=True, text=True, timeout=30, check=False)
        except (subprocess.TimeoutExpired, OSError) as exc:
            raise ContainerInfrastructureUnavailable("Docker image health probe failed or timed out") from exc
        if result.returncode or set(result.stdout.splitlines()) != set(images):
            raise ContainerInfrastructureUnavailable("required immutable images unavailable")
    return True


def require_valid_execution_files(folder):
    for path in folder.rglob("*.json"):
        if path.name not in {"execution.json", "control_execution.json"}:
            continue
        value = json.loads(path.read_bytes())
        values = value.get("runs", [])
        if is_transport_failure(value) or any(isinstance(row, dict) and "runs" in row and is_transport_failure(row) for row in values):
            raise ContainerInfrastructureUnavailable("Docker transport failure observed; cannot count as repeated software failure")
