"""Acquire strict-v5 metadata from the official SWE-bench task repo only."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import urllib.request
from pathlib import Path

import yaml

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_metadata import locally_touched_ids
from evals.e1c_strict_v5_metadata_import import freeze_source

REPO = "SWE-bench/swe-bench-tasks"
BRANCH = "main"
API = f"https://api.github.com/repos/{REPO}"
OUT = ROOT / "data" / "e1c_strict_v5_official_metadata_pool.json"
FORBIDDEN_TASK_FILES = {
    "problem_statement.md",
    "tests.json",
    "gold.patch",
    "test.patch",
    "eval.sh",
    "hints.md",
}
ALLOWED_FIELDS = ("instance_id", "repo", "base_commit", "image")


def _json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "e1c-strict-v5-official-metadata"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def branch_revision() -> str:
    payload = _json(f"{API}/branches/{BRANCH}")
    revision = payload["commit"]["sha"]
    if not isinstance(revision, str) or len(revision) != 40:
        raise ValueError("official task repo branch revision invalid")
    return revision


def task_yaml_inventory(revision: str) -> list[dict]:
    payload = _json(f"{API}/git/trees/{revision}?recursive=1")
    if payload.get("truncated"):
        raise RuntimeError("official task repo tree is truncated")
    rows = []
    for item in payload.get("tree", []):
        path = item.get("path")
        if (
            item.get("type") == "blob"
            and isinstance(path, str)
            and path.startswith("tasks/")
            and path.endswith("/task.yaml")
        ):
            parts = path.split("/")
            if len(parts) != 3:
                continue
            instance_id = parts[1]
            rows.append({
                "instance_id": instance_id,
                "task_yaml_path": path,
                "task_yaml_blob_sha": item.get("sha"),
            })
    return rows


def deterministic_candidates(inventory: list[dict], *, limit: int = 12) -> list[dict]:
    touched = locally_touched_ids()
    ranked = []
    for row in inventory:
        instance_id = row["instance_id"]
        if instance_id in touched:
            continue
        rank = hashlib.sha256(
            f"e1c-strict-v5-official-task-repo|{instance_id}".encode()
        ).hexdigest()
        ranked.append((rank, row))
    ranked.sort(key=lambda item: (item[0], item[1]["instance_id"]))
    return [row for _, row in ranked[:limit]]


def fetch_task_metadata(row: dict, revision: str) -> dict:
    path = row["task_yaml_path"]
    payload = _json(f"{API}/contents/{path}?ref={revision}")
    if payload.get("sha") != row.get("task_yaml_blob_sha"):
        raise RuntimeError(f"task.yaml blob changed for {row['instance_id']}")
    raw = base64.b64decode(payload["content"])
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError("task.yaml metadata must be an object")
    if any(name in data for name in FORBIDDEN_TASK_FILES):
        raise ValueError("task.yaml unexpectedly contains forbidden task-content key")
    projected = {field: data.get(field) for field in ALLOWED_FIELDS}
    if projected["instance_id"] != row["instance_id"]:
        raise ValueError("task.yaml instance_id does not match path identity")
    if not all(isinstance(projected[field], str) and projected[field] for field in ALLOWED_FIELDS):
        raise ValueError("task.yaml missing required strict-v5 metadata field")
    if len(projected["base_commit"]) != 40:
        raise ValueError("task.yaml base_commit invalid")
    return {
        **projected,
        "_provenance": {
            "source_repo": REPO,
            "source_revision": revision,
            "task_yaml_path": path,
            "task_yaml_blob_sha": payload["sha"],
            "task_yaml_sha256": hashlib.sha256(raw).hexdigest(),
            "forbidden_task_files_read": [],
        },
    }


def acquire(*, candidate_limit: int = 12, output: Path = OUT) -> dict:
    revision = branch_revision()
    inventory = task_yaml_inventory(revision)
    candidates = deterministic_candidates(inventory, limit=candidate_limit)
    rows = []
    provenance = {}
    for candidate in candidates:
        item = fetch_task_metadata(candidate, revision)
        instance_id = item["instance_id"]
        provenance[instance_id] = item.pop("_provenance")
        rows.append(item)
    value = {
        "schema": "e1c-strict-v5-official-metadata-pool-v1",
        "source_name": "official_swebench_task_repo_task_yaml",
        "source_repo": REPO,
        "source_revision": revision,
        "selection_rule": (
            "lowest sha256(e1c-strict-v5-official-task-repo|instance_id) "
            "after current locally-touched/prior-lineage exclusion"
        ),
        "provider_calls": 0,
        "task_content_inspected": False,
        "forbidden_task_files_read": [],
        "inventory_count": len(inventory),
        "candidate_count": len(rows),
        "tasks": rows,
        "field_provenance": provenance,
    }
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    value["pool_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


def acquire_and_freeze(*, candidate_limit: int = 12, output: Path = OUT) -> dict:
    pool = acquire(candidate_limit=candidate_limit, output=output)
    freeze_result = freeze_source(
        output,
        source_revision=pool["source_revision"],
    )
    return {
        "schema": "e1c-strict-v5-official-metadata-freeze-v1",
        "provider_calls": 0,
        "task_content_inspected": False,
        "forbidden_task_files_read": [],
        "source_revision": pool["source_revision"],
        "pool_sha256": pool["pool_sha256"],
        "candidate_count": pool["candidate_count"],
        "freeze": freeze_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("acquire", "freeze"))
    parser.add_argument("--candidate-limit", type=int, default=12)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    result = (
        acquire(candidate_limit=args.candidate_limit, output=args.output)
        if args.command == "acquire"
        else acquire_and_freeze(candidate_limit=args.candidate_limit, output=args.output)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
