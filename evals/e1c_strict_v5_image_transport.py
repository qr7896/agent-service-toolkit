"""Record strict-v5 image transport state without changing admission."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from evals.e1c_admission import ROOT

MANIFEST = ROOT / "data" / "e1c_strict_v5_canary_manifest.json"
OUT = ROOT / "data" / "e1c_strict_v5_image_transport.json"
MIRROR_PREFIX = "ghcr.io/epoch-research/swe-bench.eval.x86_64."


def _manifest(image: str, timeout: int = 45) -> dict:
    try:
        completed = subprocess.run(
            ["docker", "manifest", "inspect", "--verbose", image],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"reachable": False, "status": "timeout", "digest": None}
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout).strip()
        return {
            "reachable": False,
            "status": "transport_error",
            "digest": None,
            "error_sha256": hashlib.sha256(message.encode()).hexdigest(),
            "error_tail": message[-500:],
        }
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"reachable": False, "status": "invalid_manifest_json", "digest": None}
    descriptor = payload.get("Descriptor", {})
    return {
        "reachable": True,
        "status": "manifest_available",
        "digest": descriptor.get("digest"),
        "media_type": descriptor.get("mediaType"),
        "platform": descriptor.get("platform"),
    }


def build(output: Path = OUT, timeout: int = 45) -> dict:
    frozen = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = []
    for task in frozen["tasks"]:
        instance_id = task["instance_id"]
        official = _manifest(task["image"], timeout=timeout)
        mirror_image = f"{MIRROR_PREFIX}{instance_id}:latest"
        mirror = _manifest(mirror_image, timeout=timeout)
        rows.append(
            {
                "instance_id": instance_id,
                "official_image": task["image"],
                "official": official,
                "mirror_image": mirror_image,
                "mirror": mirror,
                "mirror_authoritative_for_admission": False,
            }
        )
    result = {
        "schema": "e1c-strict-v5-image-transport-v1",
        "provider_calls": 0,
        "changes_admission": False,
        "official_ready_count": sum(row["official"]["reachable"] for row in rows),
        "mirror_ready_count": sum(row["mirror"]["reachable"] for row in rows),
        "rows": rows,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
