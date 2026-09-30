"""Sequentially acquire frozen DEV12 images with progress and a disk stop gate.

This only downloads and imports images. It never opens grader material, runs a
model, or treats an imported image as Base/Gold admission evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from evals.e1c_evaluation_2 import ROOT
from evals.e1c_evaluation_2_mirror_acquire import archive_layout, build_layout, load_archive
from evals.e1c_evaluation_2_probe import _TRANSPORT, _TRANSPORT_SHA256, verified_mirror_image

DEFAULT_ROOT = ROOT / ".codex/e1c/evaluation_2/acquire"
HEADROOM_GIB = 20
PILOT = "marshmallow-code__marshmallow-1252"


def frozen_rows() -> list[dict]:
    raw = _TRANSPORT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != _TRANSPORT_SHA256:
        raise ValueError("DEV12 transport ledger changed after freeze")
    ledger = json.loads(raw)
    rows = ledger["rows"]
    if ledger.get("digest_identical_count") != 12 or len(rows) != 12:
        raise ValueError("DEV12 mirror transport is incomplete")
    for row in rows:
        if not row.get("digest_identical"):
            raise ValueError("DEV12 mirror manifest differs from official")
        verified_mirror_image(row["instance_id"])
    return sorted(rows, key=lambda row: (row["instance_id"] != PILOT, row["official"]["compressed_layer_bytes"]))


def _loaded(tag: str, config_digest: str) -> bool:
    completed = subprocess.run(
        ["docker", "image", "inspect", tag, "--format", "{{.Id}}"],
        capture_output=True, text=True, check=False,
    )
    return completed.returncode == 0 and completed.stdout.strip() == config_digest


def _cleanup_verified_temporary(workdir: Path, root: Path) -> None:
    """Remove only task-local generated OCI files after verified Docker load."""
    if workdir.resolve().parent != root.resolve():
        raise ValueError("temporary cleanup target escapes acquisition root")
    layout = (workdir / "layout").resolve()
    archive = (workdir / "docker_archive.tar").resolve()
    if layout.parent != workdir.resolve() or archive.parent != workdir.resolve():
        raise ValueError("temporary cleanup target escapes task directory")
    if archive.is_file():
        archive.unlink()
    if layout.is_dir():
        shutil.rmtree(layout)


def acquire_all(root: Path, *, timeout_seconds: int = 7200, max_images: int = 12) -> dict:
    if not 1 <= max_images <= 12:
        raise ValueError("max_images must be between 1 and 12")
    rows = frozen_rows()
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    completed = 0
    started = time.monotonic()
    for number, row in enumerate(rows[:max_images], 1):
        instance_id = row["instance_id"]
        workdir = root / instance_id
        if workdir.resolve().parent != root:
            raise ValueError("DEV12 task directory escapes acquisition root")
        status_path = workdir / "loaded.json"
        if status_path.is_file():
            status = json.loads(status_path.read_text(encoding="utf-8"))
            if status.get("instance_id") == instance_id and _loaded(status["local_tag"], status["config_digest"]):
                completed += 1
                print(f"[{number}/12] {instance_id}: already verified in Docker; skip", flush=True)
                _cleanup_verified_temporary(workdir, root)
                continue
        free_gib = shutil.disk_usage(root).free / 1024**3
        compressed_gib = row["official"]["compressed_layer_bytes"] / 1024**3
        required_gib = HEADROOM_GIB + 6 * compressed_gib
        print(
            f"[{number}/12] {instance_id}: {compressed_gib:.2f} GiB compressed; "
            f"D: free {free_gib:.2f} GiB; required floor {required_gib:.2f} GiB",
            flush=True,
        )
        if free_gib < required_gib:
            raise RuntimeError(f"disk stop gate: {free_gib:.2f} GiB free < {required_gib:.2f} GiB floor")
        workdir.mkdir(parents=True, exist_ok=True)
        item_started = time.monotonic()
        result = build_layout(instance_id, workdir / "layout", timeout_seconds=timeout_seconds)
        if _loaded(result["local_tag"], result["config_digest"]):
            result["load"] = {
                "local_tag": result["local_tag"],
                "loaded_config_digest": result["config_digest"],
                "docker_load_output": "already_loaded_verified",
            }
            result["duration_seconds"] = round(time.monotonic() - item_started, 1)
            status_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            completed += 1
            _cleanup_verified_temporary(workdir, root)
            print(f"[{number}/12] existing Docker image verified; no duplicate import", flush=True)
            continue
        archive = workdir / "docker_archive.tar"
        archive_layout(workdir / "layout", archive)
        result["load"] = load_archive(archive, result["config_digest"], result["local_tag"])
        result["duration_seconds"] = round(time.monotonic() - item_started, 1)
        status_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        completed += 1
        print(f"[{number}/12] verified Docker import complete in {result['duration_seconds'] / 60:.1f} min", flush=True)
        _cleanup_verified_temporary(workdir, root)
        print(f"[{number}/12] temporary OCI layout removed; D: free {shutil.disk_usage(root).free / 1024**3:.2f} GiB", flush=True)
    return {
        "schema": "e1c-evaluation-2-dev12-image-acquisition-summary-v1",
        "verified_loaded": completed,
        "total": 12,
        "duration_minutes": round((time.monotonic() - started) / 60, 1),
        "provider_calls": 0,
        "official_base_gold_admission": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--timeout-per-image", type=int, default=7200)
    parser.add_argument("--max-images", type=int, default=12)
    args = parser.parse_args()
    try:
        print(json.dumps(acquire_all(args.workdir, timeout_seconds=args.timeout_per_image, max_images=args.max_images), ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f"STOP {type(exc).__name__}: {exc}; completed images are preserved for resume", file=sys.stderr, flush=True)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
