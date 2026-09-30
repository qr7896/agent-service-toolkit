"""Metadata-only official/mirror manifest comparison for sealed E1-C canary images."""

from __future__ import annotations

import json
import re

from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_canary_metadata import OUT as METADATA
from evals.e1c_evaluation_2_canary_select import IDENTITY
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_image_transport import _manifest

OUT = ROOT / ".codex/e1c/evaluation_2/canary-v1/image_transport.json"
IMAGE = re.compile(r"swebench/(sweb\.eval\.x86_64\.[a-z0-9_.-]+):latest\Z")


def audit() -> dict:
    metadata = json.loads(METADATA.read_bytes())
    if metadata.get("identity_sha256") != _sha(IDENTITY) or len(metadata.get("tasks", [])) != 3:
        raise ValueError("canary metadata is not sealed")
    rows = []
    for task in metadata["tasks"]:
        match = IMAGE.fullmatch(task["image"])
        if not match:
            raise ValueError("unexpected canary image reference")
        repo = "swebench/" + match.group(1)
        official = _manifest(repo, mirror=False, proxy="http://127.0.0.1:7892")
        mirror = _manifest(repo, mirror=True, proxy=None, mirror_host="docker.1panel.live")
        if (official["top_digest"], official["platform_digest"]) != (mirror["top_digest"], mirror["platform_digest"]):
            raise ValueError(f"official/mirror image digest differs: {task['instance_id']}")
        rows.append({
            "instance_id": task["instance_id"], "official_image": task["image"],
            "repository": repo, "official": official, "mirror": mirror,
            "digest_identical": True,
        })
        print(json.dumps({"instance_id": task["instance_id"], "compressed_gib": round(official["compressed_layer_bytes"] / 1024**3, 2), "digest_identical": True}), flush=True)
    value = {
        "schema": "e1c2-canary-image-transport-v1",
        "identity_sha256": _sha(IDENTITY), "metadata_sha256": _sha(METADATA),
        "mirror_host": "docker.1panel.live", "official_proxy_metadata_only": True,
        "mirror_os_proxy_bypassed": True, "blob_requests": 0,
        "image_pulls": 0, "provider_calls": 0, "rows": rows,
    }
    if OUT.exists():
        if json.loads(OUT.read_bytes()) != value:
            raise ValueError("existing canary transport record differs")
    else:
        _save(OUT, value)
    return value


if __name__ == "__main__":
    result = audit()
    print(json.dumps({"verified": len(result["rows"]), "provider_calls": 0}))
