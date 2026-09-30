"""Acquire a new strict-v6 canary from official task.yaml metadata only."""

from __future__ import annotations

import hashlib
import io
import json
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

from evals.e1c_admission import ROOT
from evals.e1c_strict_v6_reserve import SALT, freeze
from evals.e1c_strict_v6_selection_boundary import denylist

REPO = "SWE-bench/swe-bench-tasks"
SOURCE_REVISION = "3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d"
INVENTORY_REPO_REVISION = "02e7a74ffd0b707aab73d203fe87bdc7c76afc8e"
INVENTORY_ARCHIVE = (
    "https://codeload.github.com/SWE-bench/SWE-bench/zip/"
    + INVENTORY_REPO_REVISION
)
TREE_URL = (
    "https://api.github.com/repos/SWE-bench/swe-bench-tasks/git/trees/"
    f"{SOURCE_REVISION}?recursive=1"
)
RAW_ROOT = f"https://raw.githubusercontent.com/{REPO}/{SOURCE_REVISION}"
POOL = ROOT / "data" / "e1c_strict_v6_official_metadata_pool.json"
MANIFEST = ROOT / "data" / "e1c_strict_v6_canary_manifest.json"
REQUIRED = ("instance_id", "repo", "base_commit", "image")


def _read_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "e1c-strict-v6-official-metadata"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("official metadata response must be an object")
    return payload


def _archive_inventory() -> list[dict]:
    request = urllib.request.Request(
        INVENTORY_ARCHIVE,
        headers={"User-Agent": "e1c-strict-v6-inventory"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read()
    archive = zipfile.ZipFile(io.BytesIO(raw))
    rows = []
    seen = set()
    for name in archive.namelist():
        parts = name.split("/")
        try:
            index = parts.index("swebench-og")
        except ValueError:
            continue
        if len(parts) <= index + 3 or parts[index + 3] != "environment.yml":
            continue
        repo_dir = parts[index + 1]
        issue_id = parts[index + 2]
        instance_id = f"{repo_dir}-{issue_id}"
        if instance_id in seen:
            continue
        seen.add(instance_id)
        rows.append({
            "instance_id": instance_id,
            "path": f"tasks/{instance_id}/task.yaml",
            "blob_sha": None,
            "inventory_source": "swebench_main_resource_zip_names_only",
            "inventory_revision": INVENTORY_REPO_REVISION,
            "inventory_archive_sha256": hashlib.sha256(raw).hexdigest(),
        })
    return sorted(rows, key=lambda row: row["instance_id"])


def inventory() -> list[dict]:
    try:
        payload = _read_json(TREE_URL)
    except urllib.error.HTTPError as exc:
        if exc.code == 403:
            return _archive_inventory()
        raise
    if payload.get("truncated"):
        raise RuntimeError("official task-repo tree is truncated")
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
            rows.append({
                "instance_id": parts[1],
                "path": path,
                "blob_sha": item.get("sha"),
                "inventory_source": "swebench_tasks_git_tree",
                "inventory_revision": SOURCE_REVISION,
            })
    return rows


def ranked_candidates(rows: list[dict], *, limit: int = 24) -> list[dict]:
    touched = denylist()
    ranked = []
    for row in rows:
        instance_id = row["instance_id"]
        if instance_id in touched:
            continue
        rank = hashlib.sha256(f"{SALT}|{instance_id}".encode()).hexdigest()
        ranked.append((rank, row))
    ranked.sort(key=lambda item: (item[0], item[1]["instance_id"]))
    return [row for _, row in ranked[:limit]]


def _fetch_yaml(path: str) -> bytes:
    request = urllib.request.Request(
        f"{RAW_ROOT}/{path}",
        headers={"User-Agent": "e1c-strict-v6-official-metadata"},
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        return response.read()


def acquire(*, candidate_limit: int = 24, output: Path = POOL) -> dict:
    candidates = ranked_candidates(inventory(), limit=candidate_limit)
    tasks = []
    provenance = {}
    errors = []
    fetched = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(_fetch_yaml, candidate["path"]): candidate
            for candidate in candidates
        }
        for future in as_completed(futures):
            candidate = futures[future]
            try:
                fetched[candidate["instance_id"]] = future.result()
            except Exception as exc:
                errors.append({
                    "instance_id": candidate["instance_id"],
                    "reason": f"{type(exc).__name__}: {exc}",
                })
    for candidate in candidates:
        raw = fetched.get(candidate["instance_id"])
        if raw is None:
            continue
        payload = yaml.safe_load(raw)
        if not isinstance(payload, dict):
            errors.append({
                "instance_id": candidate["instance_id"],
                "reason": "task_yaml_not_object",
            })
            continue
        row = {key: payload.get(key) for key in REQUIRED}
        if row["instance_id"] != candidate["instance_id"]:
            errors.append({
                "instance_id": candidate["instance_id"],
                "reason": "instance_id_mismatch",
            })
            continue
        if not all(isinstance(row[key], str) and row[key] for key in REQUIRED):
            errors.append({
                "instance_id": candidate["instance_id"],
                "reason": "required_metadata_missing",
            })
            continue
        if len(row["base_commit"]) != 40:
            errors.append({
                "instance_id": candidate["instance_id"],
                "reason": "base_commit_invalid",
            })
            continue
        tasks.append(row)
        provenance[row["instance_id"]] = {
            "source_repo": REPO,
            "source_revision": SOURCE_REVISION,
            "task_yaml_path": candidate["path"],
            "task_yaml_blob_sha": candidate.get("blob_sha"),
            "task_yaml_sha256": hashlib.sha256(raw).hexdigest(),
            "inventory_source": candidate.get("inventory_source"),
            "inventory_revision": candidate.get("inventory_revision"),
            "inventory_archive_sha256": candidate.get("inventory_archive_sha256"),
        }
        if len(tasks) >= 12:
            break
    value = {
        "schema": "e1c-strict-v6-official-metadata-pool-v1",
        "source_repo": REPO,
        "source_revision": SOURCE_REVISION,
        "selection_salt": SALT,
        "provider_calls": 0,
        "task_content_inspected": False,
        "forbidden_task_files_read": [],
        "candidate_limit": candidate_limit,
        "tasks": tasks,
        "field_provenance": provenance,
        "fetch_errors": errors,
    }
    value["pool_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


def acquire_and_freeze(*, candidate_limit: int = 24) -> dict:
    pool = acquire(candidate_limit=candidate_limit)
    result = freeze(
        pool["tasks"],
        source_revision=SOURCE_REVISION,
        output=MANIFEST,
    )
    return {
        "schema": "e1c-strict-v6-official-freeze-v1",
        "provider_calls": 0,
        "task_content_inspected": False,
        "forbidden_task_files_read": [],
        "pool_sha256": pool["pool_sha256"],
        "available_metadata_rows": len(pool["tasks"]),
        "fetch_error_count": len(pool["fetch_errors"]),
        "freeze": result,
    }


if __name__ == "__main__":
    print(json.dumps(acquire_and_freeze(), ensure_ascii=False, indent=2))
