"""Acquire the three fixed canary images from an official-digest-matched direct mirror."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time

from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_batch_acquire import _cleanup_verified_temporary
from evals.e1c_evaluation_2_canary_metadata import OUT as METADATA
from evals.e1c_evaluation_2_canary_select import IDENTITY
from evals.e1c_evaluation_2_canary_transport import OUT as TRANSPORT
from evals.e1c_evaluation_2_dev_pilot import _save, _sha
from evals.e1c_evaluation_2_mirror_acquire import archive_layout, build_layout, load_archive

OUT = ROOT / ".codex/e1c/evaluation_2/canary-v1/acquire"


def acquire(*, timeout_per_image: int = 7200) -> dict:
    identity = json.loads(IDENTITY.read_bytes())
    metadata = json.loads(METADATA.read_bytes())
    transport = json.loads(TRANSPORT.read_bytes())
    if (
        metadata["identity_sha256"] != _sha(IDENTITY)
        or transport["identity_sha256"] != _sha(IDENTITY)
        or transport["metadata_sha256"] != _sha(METADATA)
        or transport["mirror_host"] != "docker.1panel.live"
        or not (len(identity["tasks"]) == len(metadata["tasks"]) == len(transport["rows"]) == 3)
    ):
        raise ValueError("canary image transport is not bound to fixed identity")
    OUT.mkdir(parents=True, exist_ok=True)
    completed = 0
    for number, (task, meta, row) in enumerate(zip(identity["tasks"], metadata["tasks"], transport["rows"], strict=True), 1):
        iid = task["instance_id"]
        if iid != meta["instance_id"] or iid != row["instance_id"] or meta["image"] != row["official_image"] or row["digest_identical"] is not True:
            raise ValueError("canary image identity changed")
        destination = OUT / iid
        status_path = destination / "loaded.json"
        if status_path.is_file():
            old = json.loads(status_path.read_bytes())
            inspected = subprocess.run(["docker", "image", "inspect", old["local_tag"], "--format", "{{.Id}}"], capture_output=True, text=True, check=False)
            if old.get("transport_sha256") == _sha(TRANSPORT) and inspected.returncode == 0 and inspected.stdout.strip() == old["config_digest"]:
                completed += 1
                print(f"[{number}/3] {iid}: verified local image present", flush=True)
                continue
            raise ValueError("recorded canary image unavailable or differs")
        compressed_gib = row["official"]["compressed_layer_bytes"] / 1024**3
        floor = 20 + 6 * compressed_gib
        free = shutil.disk_usage(OUT).free / 1024**3
        print(f"[{number}/3] {iid}: compressed {compressed_gib:.2f} GiB; free {free:.2f} GiB; floor {floor:.2f} GiB", flush=True)
        if free < floor:
            raise RuntimeError("disk stop gate before canary image acquisition")
        destination.mkdir(exist_ok=True)
        reference = f"docker.1panel.live/{row['repository']}@{row['official']['top_digest']}"
        started = time.monotonic()
        result = build_layout(iid, destination / "layout", timeout_seconds=timeout_per_image, verified_reference=reference)
        if result["top_digest"] != row["official"]["top_digest"] or result["platform_digest"] != row["official"]["platform_digest"]:
            raise ValueError("downloaded canary manifest differs from official")
        archive = destination / "docker_archive.tar"
        archive_layout(destination / "layout", archive)
        result["load"] = load_archive(archive, result["config_digest"], result["local_tag"])
        result["transport_sha256"] = _sha(TRANSPORT)
        result["duration_seconds"] = round(time.monotonic() - started, 1)
        _save(status_path, result)
        _cleanup_verified_temporary(destination, OUT)
        completed += 1
        print(f"[{number}/3] {iid}: verified import complete", flush=True)
    return {"verified_loaded": completed, "fixed_denominator": 3, "provider_calls": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-per-image", type=int, default=7200)
    args = parser.parse_args()
    print(json.dumps(acquire(timeout_per_image=args.timeout_per_image)))
