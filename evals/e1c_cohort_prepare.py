"""Resume-safe model-free preparation status for the E1-C cohort.

This module never calls a model and never changes frozen eligibility.  It makes
the distinction between metadata candidates, recorded admission attempts, and
actually admitted tasks explicit so a registry outage cannot be mistaken for
an experimental outcome.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

from evals.e1c_materialize import OUT, select

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / ".codex" / "e1c_swebench_tree.json"
TARGET = 30


def _json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def classify(instance_id: str) -> dict:
    task_dir = OUT / "tasks" / instance_id
    if not (task_dir / "task.yaml").exists():
        return {
            "instance_id": instance_id,
            "image": None,
            "image_local": False,
            "base_recorded": False,
            "base_pass": False,
            "gold_recorded": False,
            "gold_pass": False,
            "admitted": False,
            "classification": "metadata_candidate_pending_materialization",
        }
    task = yaml.safe_load((task_dir / "task.yaml").read_text(encoding="utf-8"))
    result_dir = OUT / "admission_v2" / instance_id
    base, gold = _json(result_dir / "base.json"), _json(result_dir / "gold.json")
    image_local = subprocess.run(
        ["docker", "image", "inspect", task["image"]],
        capture_output=True,
        check=False,
    ).returncode == 0
    admitted = bool(base and gold and base.get("phase_pass") and gold.get("phase_pass"))
    source_invalid = any(
        row is not None and row.get("source_identity_valid") is False for row in (base, gold)
    )
    if admitted:
        state = "admitted"
    elif source_invalid:
        state = "task_invalid_source_identity"
    elif base is not None or gold is not None:
        state = "recorded_not_admitted"
    elif image_local:
        state = "local_image_pending_admission"
    else:
        state = "network_image_pending"
    return {
        "instance_id": instance_id,
        "image": task["image"],
        "image_local": image_local,
        "base_recorded": base is not None,
        "base_pass": bool(base and base.get("phase_pass")),
        "gold_recorded": gold is not None,
        "gold_pass": bool(gold and gold.get("phase_pass")),
        "admitted": admitted,
        "classification": state,
    }


def build_status(pool_size: int = 120, *, cache_only: bool = True) -> dict:
    frozen = json.loads((OUT / "candidate_manifest.json").read_text(encoding="utf-8"))
    pool = select(TREE, target=pool_size, cache_only=cache_only)
    frozen_ids = [row["instance_id"] for row in frozen["tasks"]]
    if [row["instance_id"] for row in pool[:len(frozen_ids)]] != frozen_ids:
        raise ValueError("discovery prefix differs from the frozen original candidate order")
    frozen_set = set(frozen_ids)
    replacements = [row for row in pool if row["instance_id"] not in frozen_set]
    attempted_candidates = [*frozen["tasks"], *replacements]
    attempts = [{**row, **classify(row["instance_id"])} for row in attempted_candidates]
    admitted = [row for row in attempts if row["admitted"]]
    status = {
        "schema": "e1c-cohort-preparation-v1",
        "target_admitted": TARGET,
        "frozen_candidate_count": len(frozen_ids),
        "admitted_count": len(admitted),
        "recorded_count": sum(row["base_recorded"] or row["gold_recorded"] for row in attempts),
        "local_image_count": sum(row["image_local"] for row in attempts),
        # Cache-only selection can skip uncached earlier candidates; it cannot
        # certify the deterministic replacement prefix, even if 30 pass.
        "ready_to_freeze_final_cohort": (
            not cache_only and len(pool) == pool_size and len(admitted) >= TARGET
        ),
        "attempts": attempts,
        "replacement_pool": replacements,
        "replacement_pool_count": len(replacements),
        "replacement_pool_partial": len(pool) < pool_size,
        "selection_mode": "cache_only" if cache_only else "network_bounded",
        "claim_boundary": "pre-live, model-free; replacement rows are metadata candidates until full frozen admission passes",
    }
    return status


def write_status(status: dict) -> None:
    path = OUT / "cohort_preparation_status.json"
    path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    if status["ready_to_freeze_final_cohort"]:
        rows = [row for row in status["attempts"] if row["admitted"]][:TARGET]
        manifest = {
            "schema": "e1c-final-admitted-cohort-v1",
            "status": "admitted_pre_live",
            "count": TARGET,
            "tasks": rows,
        }
        data = (json.dumps(manifest, indent=2) + "\n").encode()
        (OUT / "final_admitted_manifest.json").write_bytes(data)
        (OUT / "final_admitted_manifest.sha256").write_text(
            hashlib.sha256(data).hexdigest() + "\n", encoding="utf-8"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool-size", type=int, default=120)
    parser.add_argument("--allow-network", action="store_true")
    args = parser.parse_args()
    status = build_status(args.pool_size, cache_only=not args.allow_network)
    write_status(status)
    print(json.dumps({k: status[k] for k in (
        "target_admitted", "frozen_candidate_count", "admitted_count",
        "recorded_count", "local_image_count", "replacement_pool_count",
        "ready_to_freeze_final_cohort"
    )}))


if __name__ == "__main__":
    main()
