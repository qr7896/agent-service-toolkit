"""Resume-safe, model-free admission of the frozen E1-C candidate manifest."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys

import yaml

from evals.e1c_admission import ROOT, TASKS, probe

OUT = ROOT / ".codex" / "e1c"
MIN_FREE_BYTES = 12 * 1024**3


def load_rows(replacement_pool: bool = False) -> list[dict[str, str]]:
    manifest = json.loads((OUT / "candidate_manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "selected_not_admitted" or manifest["count"] != 30:
        raise ValueError("candidate manifest is not the frozen pre-admission n=30")
    if not replacement_pool:
        return manifest["tasks"]
    if any(
        not all((OUT / "admission_v2" / row["instance_id"] / f"{phase}.json").exists()
                for phase in ("base", "gold"))
        for row in manifest["tasks"]
    ):
        raise ValueError("finish recording all original 30 before replacement admission")
    status = json.loads((OUT / "cohort_preparation_status.json").read_text(encoding="utf-8"))
    rows = status["replacement_pool"]
    if (status["selection_mode"] != "network_bounded"
            or status["replacement_pool_partial"]
            or status["frozen_candidate_count"] != 30
            or not rows):
        raise ValueError("replacement pool is not a complete deterministic prefix")
    ids = [row["instance_id"] for row in rows]
    tasks = json.loads((OUT / "replacement_task_inventory.json").read_text(encoding="utf-8"))
    sources = json.loads((OUT / "replacement_source_inventory.json").read_text(encoding="utf-8"))
    if ([row["instance_id"] for row in tasks["tasks"]] != ids
            or [row["instance_id"] for row in sources["tasks"]] != ids
            or any(row["materialization_status"] != "complete" for row in tasks["tasks"])
            or any(not row["match"] for row in sources["tasks"])):
        raise ValueError("replacement files or exact source commits are not verified")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replacement-pool", action="store_true")
    args = parser.parse_args()
    if sys.platform == "win32" and not sys.flags.utf8_mode:
        raise RuntimeError("run this batch with python -X utf8")
    for index, row in enumerate(load_rows(args.replacement_pool), 1):
        instance_id = row["instance_id"]
        task = yaml.safe_load((TASKS / instance_id / "task.yaml").read_text(encoding="utf-8"))
        image = task["image"]
        results = OUT / "admission_v2" / instance_id
        if all((results / f"{phase}.json").exists() for phase in ("base", "gold")):
            print(
                json.dumps(
                    {"index": index, "instance_id": instance_id, "state": "already_recorded"}
                ),
                flush=True,
            )
            continue
        free = shutil.disk_usage(OUT).free
        if free < MIN_FREE_BYTES:
            raise RuntimeError(f"disk_free_below_12_gib_before_{instance_id}: {free}")
        if subprocess.run(
            ["docker", "image", "inspect", image], capture_output=True, check=False
        ).returncode:
            pull_log = OUT / "admission_v2" / f"{instance_id}.pull.log"
            pull_log.parent.mkdir(parents=True, exist_ok=True)
            print(
                json.dumps({"index": index, "instance_id": instance_id, "state": "pulling"}),
                flush=True,
            )
            with pull_log.open("wb") as log:
                completed = subprocess.run(
                    ["docker", "pull", "--platform", "linux/amd64", image],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=3600,
                    check=False,
                )
            if completed.returncode:
                raise RuntimeError(f"image_pull_failed_{instance_id}: see {pull_log}")
        phase_pass = {}
        for phase in ("base", "gold"):
            result_path = results / f"{phase}.json"
            result = (
                json.loads(result_path.read_text(encoding="utf-8"))
                if result_path.exists()
                else probe(instance_id, phase)
            )
            phase_pass[phase] = bool(result["phase_pass"])
            print(
                json.dumps(
                    {
                        "index": index,
                        "instance_id": instance_id,
                        "phase": phase,
                        "pass": phase_pass[phase],
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
        if not all(phase_pass.values()):
            print(json.dumps({"instance_id": instance_id, "state": "not_admitted"}), flush=True)


if __name__ == "__main__":
    main()
