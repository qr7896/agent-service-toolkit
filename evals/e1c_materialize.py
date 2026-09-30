from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".codex" / "e1c"
FROZEN_MANIFEST = ROOT / "data" / "e1c_candidate_manifest.json"
FROZEN_SHA256 = "16f86e20a296cc6e555038c0cbe336b6008d3b9252e8dc930a2d1c0a6cd9bca6"
TASK_REPO = "SWE-bench/swe-bench-tasks"
RAW = "https://raw.githubusercontent.com/SWE-bench/swe-bench-tasks/"
EXCLUDED_REPOS = {"more-itertools/more-itertools", "jazzband/prettytable"}
REQUIRED_FILES = {"task.yaml", "problem_statement.md", "tests.json", "test.patch", "gold.patch", "eval.sh", "Dockerfile"}


def _get(url: str, retries: int = 4, timeout: int = 12) -> bytes:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "e1c-materializer"})
            return urllib.request.urlopen(req, timeout=timeout).read()
        except Exception as exc:  # network boundary
            last = exc
            time.sleep(min(2**attempt, 8))
    assert last is not None
    raise last


def _field(text: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*['\"]?([^\n'\"]+)", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _rank(instance_id: str, repo: str, base_commit: str) -> str:
    return hashlib.sha256(f"{instance_id}|{repo}|{base_commit}".encode()).hexdigest()


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def _tree(tree_path: Path) -> dict[str, object]:
    tree = json.loads(tree_path.read_text(encoding="utf-8"))
    if tree.get("truncated") or not re.fullmatch(r"[0-9a-f]{40}", tree.get("sha", "")):
        raise ValueError("task repository tree is incomplete or has no immutable commit")
    return tree


def select(tree_path: Path, target: int = 30, *, cache_only: bool = False) -> list[dict[str, str]]:
    source = _tree(tree_path)
    tree = source["tree"]
    blobs = {row["path"]: row["sha"] for row in tree if row["type"] == "blob"}
    ids = sorted(
        {row["path"].split("/")[1] for row in tree if row["path"].startswith("tasks/") and row["path"].endswith("/task.yaml")}
    )
    cache = OUT / "metadata-cache"
    cache.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    seen_commits: set[tuple[str, str]] = set()
    seen_gold: set[str] = set()
    # Discovery order is content-independent instance-id hash; final rank is the preregistered
    # instance_id|repo|base_commit hash once metadata is known.
    for instance_id in sorted(ids, key=lambda value: hashlib.sha256(value.encode()).hexdigest()):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", instance_id):
            continue
        path = cache / f"{instance_id}.yaml"
        remote = f"tasks/{instance_id}/task.yaml"
        if not path.exists() or _git_blob_sha(path.read_bytes()) != blobs[remote]:
            if cache_only:
                continue
            data = _get(f"{RAW}{source['sha']}/{remote}")
            if _git_blob_sha(data) != blobs[remote]:
                raise ValueError(f"task metadata blob mismatch: {instance_id}")
            path.write_bytes(data)
        data = path.read_bytes()
        text = data.decode("utf-8")
        if "SWE-bench/SWE-bench_Verified" not in text:
            continue
        repo, base = _field(text, "repo"), _field(text, "base_commit")
        gold_sha = blobs.get(f"tasks/{instance_id}/gold.patch", "")
        present = {remote_path.removeprefix(f"tasks/{instance_id}/") for remote_path in blobs if remote_path.startswith(f"tasks/{instance_id}/")}
        if not repo or not re.fullmatch(r"[0-9a-f]{40}", base) or repo in EXCLUDED_REPOS or not REQUIRED_FILES <= present:
            continue
        tests_remote = f"tasks/{instance_id}/tests.json"
        tests_path = cache / f"{instance_id}.tests.json"
        if not tests_path.exists() or _git_blob_sha(tests_path.read_bytes()) != blobs[tests_remote]:
            if cache_only:
                continue
            tests_data = _get(f"{RAW}{source['sha']}/{tests_remote}")
            if _git_blob_sha(tests_data) != blobs[tests_remote]:
                raise ValueError(f"task tests blob mismatch: {instance_id}")
            tests_path.write_bytes(tests_data)
        tests = json.loads(tests_path.read_text(encoding="utf-8"))
        if not tests.get("FAIL_TO_PASS") or not tests.get("PASS_TO_PASS"):
            continue
        if (repo, base) in seen_commits or gold_sha in seen_gold:
            continue
        seen_commits.add((repo, base))
        seen_gold.add(gold_sha)
        rows.append({
            "instance_id": instance_id,
            "repo": repo,
            "base_commit": base,
            "version": _field(text, "version"),
            "rank_sha256": _rank(instance_id, repo, base),
            "source_identity": f"{TASK_REPO}@{source['sha']}:{remote}",
            "task_metadata_sha256": hashlib.sha256(data).hexdigest(),
            "selection_status": "selected_not_admitted",
        })
        if len(rows) == target:
            break
    return rows


def materialize(
    rows: list[dict[str, str]], tree_path: Path, inventory_name: str = "task_inventory.json"
) -> dict[str, object]:
    source = _tree(tree_path)
    available = {row["path"]: row["sha"] for row in source["tree"] if row["type"] == "blob"}
    inventory: list[dict[str, object]] = []
    for row in rows:
        iid = row["instance_id"]
        prefix = f"tasks/{iid}/"
        paths = sorted(path for path in available if path.startswith(prefix))
        task_dir = OUT / "tasks" / iid
        task_dir.mkdir(parents=True, exist_ok=True)
        files = []
        for remote in paths:
            relative = remote[len(prefix):]
            if Path(relative).is_absolute() or ".." in Path(relative).parts:
                raise ValueError(f"unsafe task path: {remote}")
            local = task_dir / relative
            local.parent.mkdir(parents=True, exist_ok=True)
            if not local.exists() or _git_blob_sha(local.read_bytes()) != available[remote]:
                data = _get(f"{RAW}{source['sha']}/{remote}")
                if _git_blob_sha(data) != available[remote]:
                    raise ValueError(f"task file blob mismatch: {remote}")
                local.write_bytes(data)
            data = local.read_bytes()
            files.append({"path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        found = {file["path"] for file in files}
        complete = len(files) == len(paths) and REQUIRED_FILES <= found
        inventory.append({
            "instance_id": iid,
            "file_count": len(files),
            "expected_file_count": len(paths),
            "required_file_completeness": REQUIRED_FILES <= found,
            "materialization_status": "complete" if complete else "incomplete",
            "files": files,
        })
        result = {"schema": "e1c-materialization-v1", "task_repo": f"{TASK_REPO}@{source['sha']}", "count": len(rows), "tasks": inventory}
        (OUT / inventory_name).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def _git(*args: str, cwd: Path, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)


def _git_retry(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    for attempt in range(3):
        result = _git(*args, cwd=cwd)
        if result.returncode == 0:
            return result
        if attempt < 2:
            time.sleep(2**attempt)
    return result


def materialize_sources(
    rows: list[dict[str, str]], inventory_name: str = "source_inventory.json"
) -> dict[str, object]:
    inventory: list[dict[str, object]] = []
    for row in rows:
        repo, commit, iid = row["repo"], row["base_commit"], row["instance_id"]
        repo_key = repo.replace("/", "__")
        cache = OUT / "repo-cache" / repo_key
        workspace = OUT / "repos" / repo_key / commit
        record: dict[str, object] = {
            "instance_id": iid,
            "repo": repo,
            "expected_base_commit": commit,
            "actual_base_commit": None,
            "match": False,
            "materialization_method": "git-depth1-filter-blob-none-worktree",
            "archive_source_sha256": None,
            "workspace_path": str(workspace.resolve()),
        }
        try:
            if not (cache / ".git" / "HEAD").exists():
                cache.mkdir(parents=True, exist_ok=True)
                result = _git("init", "-q", cwd=cache)
                if result.returncode:
                    raise RuntimeError(f"git init: {result.stderr[-500:]}")
                result = _git("remote", "add", "origin", f"https://github.com/{repo}.git", cwd=cache)
                if result.returncode:
                    raise RuntimeError(f"git remote: {result.stderr[-500:]}")
            present = _git("cat-file", "-e", f"{commit}^{{commit}}", cwd=cache).returncode == 0
            if not present:
                result = _git_retry(
                    "-c", "http.lowSpeedLimit=1", "-c", "http.lowSpeedTime=30",
                    "fetch", "-q", "--depth=1", "--filter=blob:none", "origin", commit,
                    cwd=cache,
                )
                if result.returncode:
                    result = _git_retry("fetch", "-q", "--depth=1", "--no-filter", "origin", commit, cwd=cache)
                    record["materialization_method"] = "git-depth1-full-worktree"
                    if result.returncode:
                        raise RuntimeError(f"git fetch: {result.stderr[-500:]}")
            if not workspace.exists():
                workspace.parent.mkdir(parents=True, exist_ok=True)
                result = _git_retry(
                    "-c", "http.lowSpeedLimit=1", "-c", "http.lowSpeedTime=30",
                    "worktree", "add", "-q", "--detach", str(workspace), commit, cwd=cache,
                )
                if result.returncode:
                    result = _git_retry("fetch", "-q", "--depth=1", "--no-filter", "origin", commit, cwd=cache)
                    record["materialization_method"] = "git-depth1-full-worktree"
                    if result.returncode:
                        raise RuntimeError(f"git full fetch: {result.stderr[-500:]}")
                    if not workspace.exists():
                        result = _git_retry("worktree", "add", "-q", "--detach", str(workspace), commit, cwd=cache)
                    if result.returncode:
                        raise RuntimeError(f"git worktree: {result.stderr[-500:]}")
            result = _git("rev-parse", "HEAD", cwd=workspace)
            record["actual_base_commit"] = result.stdout.strip() if result.returncode == 0 else None
            record["match"] = record["actual_base_commit"] == commit
            if not record["match"]:
                raise RuntimeError("workspace HEAD differs from expected base commit")
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            record["error"] = str(exc)[-500:]
        inventory.append(record)
        result = {"schema": "e1c-source-inventory-v1", "count": len(rows), "verified": sum(bool(item["match"]) for item in inventory), "tasks": inventory}
        (OUT / inventory_name).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"source_progress": len(inventory), "verified": result["verified"], "instance_id": iid, "match": record["match"]}), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", type=Path, default=ROOT / ".codex" / "e1c_swebench_tree.json")
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--frozen", action="store_true", help="Rehydrate the checked-in candidate identity without reselection")
    parser.add_argument("--replacement-pool", action="store_true", help="Materialize the fully selected replacement pool separately")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.replacement_pool:
        if args.frozen:
            raise SystemExit("--replacement-pool cannot be combined with --frozen")
        status = json.loads((OUT / "cohort_preparation_status.json").read_text(encoding="utf-8"))
        if status["selection_mode"] != "network_bounded" or status["replacement_pool_partial"]:
            raise SystemExit("replacement pool lacks a complete deterministic selection prefix")
        rows = status["replacement_pool"]
        if args.source_only:
            result = materialize_sources(rows, "replacement_source_inventory.json")
            print(json.dumps({"replacement_sources_verified": result["verified"], "count": len(rows)}))
        else:
            if _tree(args.tree)["sha"] != json.loads((OUT / "candidate_manifest.json").read_text(encoding="utf-8"))["source_tree_sha"]:
                raise SystemExit("replacement tree differs from original candidate source")
            result = materialize(rows, args.tree, "replacement_task_inventory.json")
            print(json.dumps({"replacement_tasks_materialized": sum(t["materialization_status"] == "complete" for t in result["tasks"]), "count": len(rows)}))
        return
    if args.source_only:
        manifest = json.loads((OUT / "candidate_manifest.json").read_text(encoding="utf-8"))
        if manifest.get("status") != "selected_not_admitted" or manifest.get("count") != 30:
            raise SystemExit("source materialization requires a frozen 30-task candidate manifest")
        materialize_sources(manifest["tasks"])
        return
    if args.frozen:
        # The checked-in snapshot uses portable LF; the original frozen
        # manifest was serialized with CRLF. Restore those exact bytes.
        data = FROZEN_MANIFEST.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
        if hashlib.sha256(data).hexdigest() != FROZEN_SHA256:
            raise SystemExit("checked-in candidate manifest differs from frozen identity")
        manifest = json.loads(data)
        manifest_path = OUT / "candidate_manifest.json"
        if manifest_path.exists() and manifest_path.read_bytes() != data:
            raise SystemExit("local candidate manifest differs from frozen identity")
        if not args.tree.exists():
            args.tree.parent.mkdir(parents=True, exist_ok=True)
            url = f"https://api.github.com/repos/SWE-bench/swe-bench-tasks/git/trees/{manifest['source_tree_sha']}?recursive=1"
            tree_data = _get(url)
            args.tree.write_bytes(tree_data)
        if _tree(args.tree)["sha"] != manifest["source_tree_sha"]:
            raise SystemExit("task tree differs from frozen identity")
        manifest_path.write_bytes(data)
        (OUT / "candidate_manifest.sha256").write_text(FROZEN_SHA256 + "\n", encoding="utf-8")
        inventory = materialize(manifest["tasks"], args.tree)
        print(json.dumps({"selected": 30, "materialized": sum(t["materialization_status"] == "complete" for t in inventory["tasks"])}))
        return
    rows = select(args.tree)
    if len(rows) != 30:
        raise SystemExit(f"selection incomplete: {len(rows)}/30; rerun resumes cached metadata")
    manifest = {"schema": "e1c-n30-candidate-manifest-v1", "status": "selected_not_admitted", "source_tree_sha": _tree(args.tree)["sha"], "count": 30, "tasks": rows}
    manifest_path = OUT / "candidate_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (OUT / "candidate_manifest.sha256").write_text(hashlib.sha256(manifest_path.read_bytes()).hexdigest() + "\n", encoding="utf-8")
    inventory = materialize(rows, args.tree)
    print(json.dumps({"selected": 30, "materialized": sum(t["materialization_status"] == "complete" for t in inventory["tasks"])}, indent=2))


if __name__ == "__main__":
    main()
