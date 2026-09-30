"""Materialize and assess the frozen strict-v6 canary without provider calls."""

from __future__ import annotations

import base64
import hashlib
import json
import urllib.request
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_postfreeze import materialize_source
from evals.e1c_strict_v6_runtime import build_bundle
from evals.e1c_strict_v6_selection_boundary import build as build_selection_boundary

MANIFEST = ROOT / "data" / "e1c_strict_v6_canary_manifest.json"
PREREG = ROOT / "data" / "e1c_strict_v6_prereg.json"
BOUNDARY = ROOT / "data" / "e1c_strict_v6_selection_boundary.json"
ROOT_OUT = ROOT / ".codex" / "e1c" / "strict-v6" / "postfreeze-v1"
SUMMARY = ROOT / "data" / "e1c_strict_v6_postfreeze_assessment.json"
TASK_REPO = "SWE-bench/swe-bench-tasks"
EXPECTED_SCHEMA = "e1c-strict-v6-external-canary-reserve-v1"
REQUIRED_KEYS = {"instance_id", "repo", "base_commit", "image"}


def certify_identity() -> dict:
    if not MANIFEST.is_file() or not PREREG.is_file() or not BOUNDARY.is_file():
        return {"ready": False, "reason": "v6_freeze_artifact_missing"}
    manifest_bytes = MANIFEST.read_bytes()
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    current_boundary = build_selection_boundary()
    rows = manifest.get("tasks")
    checks = {
        "manifest_schema": manifest.get("schema") == EXPECTED_SCHEMA,
        "exact_task_count": isinstance(rows, list) and len(rows) == 3,
        "identity_frozen_before_statement": (
            manifest.get("identity_frozen_before_statement_materialization") is True
        ),
        "manifest_provider_calls_zero": manifest.get("provider_calls") == 0,
        "manifest_task_content_inspected_false": manifest.get("task_content_inspected") is False,
        "prereg_provider_calls_zero": prereg.get("provider_calls") == 0,
        "live_before_admission_forbidden": prereg.get("live_allowed_before_admission") is False,
        "selection_salt_matches": (
            prereg.get("selection_salt")
            == manifest.get("selection_salt")
            == boundary.get("selection_salt")
        ),
        "source_revision_matches_boundary": (
            manifest.get("source_revision") == boundary.get("task_repo_revision")
        ),
        "boundary_current": boundary == current_boundary,
    }
    ids: list[str] = []
    rows_valid = True
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict) or set(row) != REQUIRED_KEYS:
            rows_valid = False
            continue
        if not all(isinstance(row.get(key), str) and row[key] for key in REQUIRED_KEYS):
            rows_valid = False
            continue
        if len(row["base_commit"]) != 40:
            rows_valid = False
        ids.append(row["instance_id"])
    checks["exact_metadata_schema"] = rows_valid
    checks["unique_identities"] = len(ids) == len(set(ids)) == 3
    ready = all(checks.values())
    return {
        "ready": ready,
        "reason": "strict_v6_identity_certified" if ready else "strict_v6_identity_integrity_failed",
        "checks": checks,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "instance_ids": ids,
        "source_revision": manifest.get("source_revision"),
    }


def fetch_statement(instance_id: str, revision: str) -> tuple[str, str]:
    path = f"tasks/{instance_id}/problem_statement.md"
    raw_url = (
        f"https://raw.githubusercontent.com/{TASK_REPO}/{revision}/"
        f"{path}"
    )
    api_url = f"https://api.github.com/repos/{TASK_REPO}/contents/{path}?ref={revision}"
    attempts = (
        (raw_url, False),
        (raw_url, False),
        (api_url, True),
    )
    errors = []
    raw = None
    for url, encoded in attempts:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "e1c-strict-v6-postfreeze",
                "Accept": "application/vnd.github+json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read()
            if encoded:
                document = json.loads(payload.decode("utf-8"))
                raw = base64.b64decode(document["content"])
            else:
                raw = payload
            break
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
    if raw is None:
        raise RuntimeError("statement_fetch_failed: " + " | ".join(errors))
    text = raw.decode("utf-8")
    return text, hashlib.sha256(raw).hexdigest()


def run(output: Path = SUMMARY) -> dict:
    certificate = certify_identity()
    if not certificate["ready"]:
        value = {
            "schema": "e1c-strict-v6-postfreeze-assessment-v1",
            "ready": False,
            "reason": certificate["reason"],
            "provider_calls": 0,
            "live_model_run": False,
            "rows": [],
            "certificate": certificate,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return value

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    revision = certificate["source_revision"]
    rows = []
    for task in manifest["tasks"]:
        instance_id = task["instance_id"]
        task_root = ROOT_OUT / instance_id
        statement, statement_sha = fetch_statement(instance_id, revision)
        statement_path = task_root / "problem_statement.md"
        statement_path.parent.mkdir(parents=True, exist_ok=True)
        statement_path.write_text(statement, encoding="utf-8")
        source = materialize_source(task, task_root / "source")
        if source["ready"]:
            try:
                bundle = build_bundle(
                    statement=statement,
                    workspace=task_root / "source",
                    base_commit=task["base_commit"],
                    forbidden_values=(instance_id, task["image"]),
                )
                projection_status = "supported"
                error = None
            except Exception as exc:
                bundle = None
                projection_status = "unsupported"
                error = f"{type(exc).__name__}: {exc}"
        else:
            bundle = None
            projection_status = "not_run_source_incomplete"
            error = None
        witness_status = (
            bundle["witness_plan"]["status"] if isinstance(bundle, dict) else "not_available"
        )
        candidate_count = (
            len(bundle["witness_plan"]["witnesses"]) if isinstance(bundle, dict) else 0
        )
        item = {
            "instance_id": instance_id,
            "base_commit": task["base_commit"],
            "statement_sha256": statement_sha,
            "statement_path": statement_path.relative_to(ROOT).as_posix(),
            "source": source,
            "projection_status": projection_status,
            "projection_error": error,
            "witness_status": witness_status,
            "candidate_witness_count": candidate_count,
            "bundle": bundle,
            "provider_calls": 0,
            "live_model_run": False,
            "forbidden_task_files_read": [],
        }
        item["row_sha256"] = hashlib.sha256(
            json.dumps(item, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        rows.append(item)

    candidate_rows = sum(row["candidate_witness_count"] > 0 for row in rows)
    source_ready = sum(bool(row["source"]["ready"]) for row in rows)
    projection_supported = sum(row["projection_status"] == "supported" for row in rows)
    value = {
        "schema": "e1c-strict-v6-postfreeze-assessment-v1",
        "ready": source_ready == 3 and projection_supported == 3,
        "reason": (
            "ready_for_image_and_official_admission"
            if source_ready == 3 and projection_supported == 3 and candidate_rows >= 2
            else "seal_pre_live_insufficient_candidate_reproducers"
            if source_ready == 3 and projection_supported == 3
            else "postfreeze_materialization_incomplete"
        ),
        "provider_calls": 0,
        "live_model_run": False,
        "identity_certificate": certificate,
        "source_ready_count": source_ready,
        "projection_supported_count": projection_supported,
        "candidate_reproducer_task_count": candidate_rows,
        "minimum_candidate_reproducer_tasks": 2,
        "image_pull_allowed_by_candidate_gate": candidate_rows >= 2,
        "official_admission_allowed_by_candidate_gate": candidate_rows >= 2,
        "live_allowed": False,
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
