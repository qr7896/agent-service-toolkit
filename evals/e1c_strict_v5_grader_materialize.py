"""Materialize frozen-canary grading artifacts into a grader-only boundary."""

from __future__ import annotations

import base64
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_freeze_certificate import certify

REPO = "SWE-bench/swe-bench-tasks"
RAW = f"https://raw.githubusercontent.com/{REPO}"
MANIFEST = ROOT / "data" / "e1c_strict_v5_canary_manifest.json"
OUT_ROOT = ROOT / ".codex" / "e1c" / "strict-v5" / "grader-only-v1"
SUMMARY = ROOT / "data" / "e1c_strict_v5_grader_materialization.json"
FILES = ("tests.json", "gold.patch", "test.patch", "eval.sh", "Dockerfile")


def _fetch(path: str, revision: str) -> dict:
    url = f"https://api.github.com/repos/{REPO}/contents/{path}?ref={revision}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "e1c-strict-v5-grader-materialize", "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            payload = json.load(response)
        raw = base64.b64decode(payload["content"])
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"status": "missing", "raw": None, "error": None}
        if exc.code == 403:
            fallback = urllib.request.Request(
                f"{RAW}/{revision}/{path}",
                headers={"User-Agent": "e1c-strict-v5-grader-materialize"},
            )
            try:
                with urllib.request.urlopen(fallback, timeout=12) as response:
                    return {"status": "materialized", "raw": response.read(), "error": None}
            except urllib.error.HTTPError as fallback_exc:
                if fallback_exc.code == 404:
                    return {"status": "missing", "raw": None, "error": None}
                return {
                    "status": "network_error",
                    "raw": None,
                    "error": f"HTTPError:{exc.code};raw_HTTPError:{fallback_exc.code}",
                }
            except (OSError, TimeoutError) as fallback_exc:
                return {
                    "status": "network_error",
                    "raw": None,
                    "error": (
                        f"HTTPError:{exc.code};raw_{type(fallback_exc).__name__}: {fallback_exc}"
                    ),
                }
        return {
            "status": "network_error",
            "raw": None,
            "error": f"HTTPError:{exc.code}",
        }
    except (OSError, TimeoutError) as exc:
        return {
            "status": "network_error",
            "raw": None,
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {"status": "materialized", "raw": raw, "error": None}


def run(output: Path = SUMMARY) -> dict:
    certificate = certify(output=None)
    if not certificate["ready"]:
        return {
            "schema": "e1c-strict-v5-grader-materialization-v1",
            "ready": False,
            "reason": "identity_freeze_not_certified",
            "provider_calls": 0,
            "repair_visible": False,
            "rows": [],
        }
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    revision = manifest["source_revision"]
    rows = []
    for task in manifest["tasks"]:
        instance_id = task["instance_id"]
        destination = OUT_ROOT / instance_id
        destination.mkdir(parents=True, exist_ok=True)
        files = []
        for name in FILES:
            target = destination / name
            if target.is_file():
                raw = target.read_bytes()
                files.append({
                    "name": name,
                    "present": True,
                    "status": "already_materialized",
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "blob_sha": None,
                })
                continue
            fetched = _fetch(f"tasks/{instance_id}/{name}", revision)
            raw = fetched["raw"]
            if raw is None:
                files.append({
                    "name": name,
                    "present": False,
                    "status": fetched["status"],
                    "error": fetched["error"],
                })
                continue
            target.write_bytes(raw)
            files.append({
                "name": name,
                "present": True,
                "status": "materialized",
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "blob_sha": None,
            })
        rows.append({
            "instance_id": instance_id,
            "grader_only_path": destination.as_posix(),
            "repair_visible": False,
            "files": files,
        })
    value = {
        "schema": "e1c-strict-v5-grader-materialization-v1",
        "ready": all(
            any(item["name"] == "tests.json" and item["present"] for item in row["files"])
            and any(item["name"] == "eval.sh" and item["present"] for item in row["files"])
            for row in rows
        ),
        "reason": (
            "grader_artifacts_materialized"
            if rows
            and all(
                any(item["name"] == "tests.json" and item["present"] for item in row["files"])
                and any(item["name"] == "eval.sh" and item["present"] for item in row["files"])
                for row in rows
            )
            else "grader_artifacts_incomplete"
            if rows
            else "no_rows"
        ),
        "provider_calls": 0,
        "repair_visible": False,
        "source_revision": revision,
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
