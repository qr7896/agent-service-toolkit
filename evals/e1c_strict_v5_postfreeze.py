"""Post-freeze source/image materialization for the fixed strict-v5 canary."""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_freeze_certificate import certify

MANIFEST = ROOT / "data" / "e1c_strict_v5_canary_manifest.json"
ROOT_OUT = ROOT / ".codex" / "e1c" / "strict-v5" / "postfreeze-v1"
SUMMARY = ROOT / "data" / "e1c_strict_v5_postfreeze_identity.json"


def _run(args: list[str], *, cwd: Path | None = None, timeout: int = 120) -> dict:
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "exit_code": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "exit_code": None,
            "stdout": exc.stdout[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr": exc.stderr[-4000:] if isinstance(exc.stderr, str) else "",
            "timed_out": True,
        }
    except OSError as exc:
        return {
            "exit_code": None,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
            "timed_out": False,
        }


def _git_head(path: Path) -> str | None:
    result = _run(["git", "rev-parse", "HEAD"], cwd=path, timeout=30)
    if result["exit_code"] != 0:
        return None
    return result["stdout"].strip()


def _github_archive(repo: str, base_commit: str, destination: Path) -> dict:
    archive_url = f"https://codeload.github.com/{repo}/zip/{base_commit}"
    request = urllib.request.Request(
        archive_url,
        headers={"User-Agent": "e1c-strict-v5-postfreeze"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read()
    except Exception as exc:
        return {
            "ready": False,
            "status": "github_archive_download_failed",
            "detail": f"{type(exc).__name__}: {exc}",
        }
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        roots = {name.split("/", 1)[0] for name in names if "/" in name}
        if len(roots) != 1:
            return {"ready": False, "status": "github_archive_root_invalid"}
        root = next(iter(roots))
        for member in archive.infolist():
            name = member.filename
            if not name.startswith(root + "/"):
                continue
            relative = Path(name[len(root) + 1 :])
            if not relative.parts:
                continue
            if relative.is_absolute() or ".." in relative.parts:
                return {"ready": False, "status": "github_archive_path_escape"}
            target = destination / relative
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("wb") as sink:
                shutil.copyfileobj(source, sink)
    return {
        "ready": True,
        "status": "github_archive_materialized",
        "repo_url": f"https://github.com/{repo}",
        "head": base_commit,
        "base_commit": base_commit,
        "commit_tree_sha": None,
        "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "archive_bytes": len(raw),
    }


def materialize_source(row: dict, destination: Path) -> dict:
    repo = row["repo"]
    base_commit = row["base_commit"]
    expected_url = f"https://github.com/{repo}.git"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_dir() and (destination / ".git").is_dir():
        head = _git_head(destination)
        if head == base_commit:
            return {
                "ready": True,
                "status": "already_materialized",
                "repo_url": expected_url,
                "head": head,
                "base_commit": base_commit,
            }
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    init = _run(["git", "init"], cwd=destination, timeout=30)
    if init["exit_code"] != 0:
        return {"ready": False, "status": "git_init_failed", "detail": init}
    remote = _run(["git", "remote", "add", "origin", expected_url], cwd=destination, timeout=30)
    if remote["exit_code"] != 0:
        return {"ready": False, "status": "git_remote_failed", "detail": remote}
    fetch = _run(
        ["git", "fetch", "--depth", "1", "origin", base_commit],
        cwd=destination,
        timeout=180,
    )
    if fetch["exit_code"] != 0:
        fallback = _github_archive(repo, base_commit, destination)
        return {
            **fallback,
            "git_fetch_status": "failed_then_github_archive_fallback",
            "git_fetch_detail": fetch,
        }
    checkout = _run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=destination, timeout=60)
    head = _git_head(destination)
    ready = checkout["exit_code"] == 0 and head == base_commit
    if not ready:
        fallback = _github_archive(repo, base_commit, destination)
        return {
            **fallback,
            "git_checkout_status": "failed_then_github_archive_fallback",
            "git_checkout_detail": checkout,
        }
    return {
        "ready": ready,
        "status": "materialized",
        "repo_url": expected_url,
        "head": head,
        "base_commit": base_commit,
        "fetch": fetch,
        "checkout": checkout,
    }


def inspect_image(image: str) -> dict:
    if shutil.which("docker") is None:
        return {
            "ready": False,
            "status": "docker_cli_missing",
            "image": image,
            "digest": None,
        }
    local = _run(
        ["docker", "image", "inspect", image, "--format", "{{json .RepoDigests}}"],
        timeout=30,
    )
    if local["exit_code"] == 0:
        try:
            digests = json.loads(local["stdout"].strip())
        except json.JSONDecodeError:
            digests = []
        digest = digests[0] if digests else None
        return {
            "ready": bool(digest),
            "status": "local_image_digest" if digest else "local_image_without_digest",
            "image": image,
            "digest": digest,
            "detail": local,
        }
    manifest = _run(["docker", "manifest", "inspect", image], timeout=90)
    digest = None
    if manifest["exit_code"] == 0:
        try:
            payload = json.loads(manifest["stdout"])
            digest = payload.get("Descriptor", {}).get("digest")
            if not digest:
                config = payload.get("config", {})
                digest = config.get("digest") if isinstance(config, dict) else None
        except json.JSONDecodeError:
            pass
    return {
        "ready": manifest["exit_code"] == 0,
        "status": "remote_manifest_resolved" if manifest["exit_code"] == 0 else "image_manifest_unavailable",
        "image": image,
        "digest": digest,
        "detail": manifest,
    }


def run(output: Path = SUMMARY) -> dict:
    certificate = certify(output=None)
    if not certificate["ready"]:
        return {
            "schema": "e1c-strict-v5-postfreeze-identity-v1",
            "ready": False,
            "reason": "identity_freeze_not_certified",
            "provider_calls": 0,
            "rows": [],
        }
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = []
    for row in manifest["tasks"]:
        instance_id = row["instance_id"]
        task_root = ROOT_OUT / instance_id
        source = materialize_source(row, task_root / "source")
        image = inspect_image(row["image"])
        item = {
            "instance_id": instance_id,
            "repo": row["repo"],
            "base_commit": row["base_commit"],
            "image": row["image"],
            "source": source,
            "image_identity": image,
            "provider_calls": 0,
            "forbidden_task_files_read": [],
        }
        item["row_sha256"] = hashlib.sha256(
            json.dumps(item, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        rows.append(item)
    value = {
        "schema": "e1c-strict-v5-postfreeze-identity-v1",
        "ready": all(row["source"]["ready"] and row["image_identity"]["ready"] for row in rows),
        "reason": (
            "source_and_image_identity_ready"
            if all(row["source"]["ready"] and row["image_identity"]["ready"] for row in rows)
            else "source_or_image_identity_incomplete"
        ),
        "provider_calls": 0,
        "new_task_tree_touched": False,
        "rows": rows,
    }
    value["summary_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
