"""Direct-only, zero-model infrastructure stages for the fixed second canary."""

from __future__ import annotations

import argparse
import json
import re
import urllib.request

from evals import e1c_evaluation_2_admission as admission
from evals import e1c_evaluation_2_canary_acquire as acquire
from evals import e1c_evaluation_2_canary_materialize as materialize
from evals import e1c_evaluation_2_canary_metadata as metadata
from evals import e1c_evaluation_2_canary_transport as transport
from evals import e1c_evaluation_2_probe as probe
from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_canary_v2_select import FREEZE, IDENTITY, method
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_image_transport import _manifest

OUT = ROOT / ".codex/e1c/evaluation_2/canary-v2"
METADATA = OUT / "metadata.json"
TRANSPORT = OUT / "image_transport.json"
ACQUIRE = OUT / "acquire"
GRADER = OUT / "grader-only"
PUBLIC = OUT / "issue-only"
SOURCE = OUT / "source"


def bind() -> None:
    """Reuse frozen v1 plumbing in this process without rewriting its identity."""
    metadata.FREEZE, metadata.IDENTITY, metadata.OUT, metadata.method = FREEZE, IDENTITY, METADATA, method
    transport.METADATA, transport.IDENTITY, transport.OUT = METADATA, IDENTITY, TRANSPORT
    acquire.METADATA, acquire.TRANSPORT, acquire.IDENTITY, acquire.OUT = METADATA, TRANSPORT, IDENTITY, ACQUIRE
    materialize.IDENTITY, materialize.METADATA = IDENTITY, METADATA
    materialize.TRANSPORT, materialize.ACQUIRE = TRANSPORT, ACQUIRE
    materialize.OUT, materialize.PUBLIC = OUT, PUBLIC
    materialize.SOURCE, materialize.GRADER = SOURCE, GRADER
    probe.IDENTITY, probe._ACQUIRE, probe.verified_local_image = IDENTITY, ACQUIRE, materialize.verified_image
    admission.IDENTITY, admission.METADATA = IDENTITY, METADATA
    admission.OUT, admission.TREE = GRADER, GRADER / "frozen-task-blobs.json"
    admission.verified_local_image = materialize.verified_image


def audit_direct() -> dict:
    """Compare official/mirror manifests with explicit empty proxy settings."""
    rows = json.loads(METADATA.read_bytes())
    if rows.get("identity_sha256") != _sha(IDENTITY) or len(rows.get("tasks", [])) != 3:
        raise ValueError("official metadata identity changed")
    result_rows = []
    for task in rows["tasks"]:
        match = re.fullmatch(r"swebench/(sweb\.eval\.x86_64\.[a-z0-9_.-]+):latest", task["image"])
        if not match:
            raise ValueError("unexpected official image reference")
        repo = "swebench/" + match.group(1)
        official = _manifest(repo, mirror=False, proxy=None)
        mirror = _manifest(repo, mirror=True, proxy=None, mirror_host="docker.1panel.live")
        if (official["top_digest"], official["platform_digest"]) != (mirror["top_digest"], mirror["platform_digest"]):
            raise ValueError(f"official/mirror manifest differs: {task['instance_id']}")
        result_rows.append({
            "instance_id": task["instance_id"], "official_image": task["image"],
            "repository": repo, "official": official, "mirror": mirror, "digest_identical": True,
        })
        print(json.dumps({"instance_id": task["instance_id"], "compressed_gib": round(official["compressed_layer_bytes"] / 1024**3, 2)}), flush=True)
    value = {
        "schema": "e1c2-canary-image-transport-v2", "identity_sha256": _sha(IDENTITY),
        "metadata_sha256": _sha(METADATA), "mirror_host": "docker.1panel.live",
        "official_proxy_metadata_only": False, "mirror_os_proxy_bypassed": True,
        "blob_requests": 0, "image_pulls": 0, "provider_calls": 0, "rows": result_rows,
    }
    if TRANSPORT.exists():
        if json.loads(TRANSPORT.read_bytes()) != value:
            raise ValueError("transport record changed")
    else:
        _save(TRANSPORT, value)
    return value


def admit(timeout: int) -> dict:
    outcomes = []
    for task in materialize.rows():
        for phase in ("base", "gold"):
            print(f"canary v2 admission {len(outcomes) + 1}/6: {task['instance_id']} {phase}", flush=True)
            row = admission.run_phase(task["instance_id"], phase, timeout=timeout)
            outcomes.append({key: row[key] for key in ("instance_id", "phase", "phase_pass", "returncode")})
            print(json.dumps(outcomes[-1]), flush=True)
    return {"phase_count": len(outcomes), "dual_admitted": sum(all(row["phase_pass"] for row in outcomes[n:n + 2]) for n in (0, 2, 4)), "provider_calls": 0}


def public() -> list[dict]:
    outcomes = []
    for task in materialize.rows():
        iid = task["instance_id"]
        phases = [GRADER / iid / f"{phase}.json" for phase in ("base", "gold")]
        if not all(path.is_file() and json.loads(path.read_bytes()).get("phase_pass") is True for path in phases):
            outcomes.append({"instance_id": iid, "status": "fixed_denominator_official_admission_failed"})
        else:
            outcomes.append(materialize.materialize_public(iid))
        print(json.dumps(outcomes[-1], ensure_ascii=False), flush=True)
    return outcomes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("metadata", "transport", "download", "admit", "public"))
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--timeout-per-image", type=int, default=7200)
    args = parser.parse_args()
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    bind()
    if args.command == "metadata":
        result = metadata.acquire()
    elif args.command == "transport":
        result = audit_direct()
    elif args.command == "download":
        result = acquire.acquire(timeout_per_image=args.timeout_per_image)
    elif args.command == "admit":
        result = admit(args.timeout)
    else:
        result = public()
    print(json.dumps(result, ensure_ascii=False))
