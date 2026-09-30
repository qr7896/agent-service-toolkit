"""Post-freeze zero-provider assessment for the independent strict-v7 canary."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_postfreeze import materialize_source
from evals.e1c_strict_v6_postfreeze import fetch_statement
from evals.e1c_strict_v6_runtime import build_bundle
from evals.e1c_strict_v7_prereg import build as build_prereg
from evals.e1c_strict_v7_probe import freeze_typed_plan
from evals.e1c_strict_v7_selection_boundary import build as build_boundary

MANIFEST = ROOT / "data" / "e1c_strict_v7_canary_manifest.json"
PREREG = ROOT / "data" / "e1c_strict_v7_prereg.json"
BOUNDARY = ROOT / "data" / "e1c_strict_v7_selection_boundary.json"
ROOT_OUT = ROOT / ".codex" / "e1c" / "strict-v7" / "postfreeze-v1"
OUT = ROOT / "data" / "e1c_strict_v7_postfreeze_assessment.json"


def fetch_statement_bounded(instance_id: str, revision: str, cache_path: Path) -> tuple[str, str]:
    """Fetch one frozen public statement with a bounded curl-first transport.

    The task identity and revision are already frozen. Reusing an existing exact-path
    statement is preferred so interrupted assessments are resumable without reopening
    selection or changing task identity.
    """
    if cache_path.is_file():
        raw = cache_path.read_bytes()
        return raw.decode("utf-8"), hashlib.sha256(raw).hexdigest()

    curl = shutil.which("curl.exe") or shutil.which("curl")
    if curl:
        url = (
            "https://raw.githubusercontent.com/SWE-bench/swe-bench-tasks/"
            f"{revision}/tasks/{instance_id}/problem_statement.md"
        )
        try:
            completed = subprocess.run(
                [curl, "-L", "--fail", "--silent", "--show-error", "--max-time", "20", url],
                check=False,
                capture_output=True,
                timeout=25,
            )
        except (OSError, subprocess.TimeoutExpired):
            completed = None
        if completed is not None and completed.returncode == 0 and completed.stdout:
            raw = completed.stdout
            return raw.decode("utf-8"), hashlib.sha256(raw).hexdigest()

    return fetch_statement(instance_id, revision)


def certify_identity() -> dict:
    manifest_raw = MANIFEST.read_bytes()
    prereg_raw = PREREG.read_bytes()
    boundary_raw = BOUNDARY.read_bytes()
    manifest = json.loads(manifest_raw.decode("utf-8"))
    prereg = json.loads(prereg_raw.decode("utf-8"))
    boundary = json.loads(boundary_raw.decode("utf-8"))
    current_prereg = build_prereg()
    current_boundary = build_boundary()
    rows = manifest.get("tasks")
    checks = {
        "manifest_schema": manifest.get("schema") == "e1c-strict-v7-external-canary-reserve-v1",
        "exact_task_count": isinstance(rows, list) and len(rows) == 3,
        "identity_frozen_before_statement": manifest.get("identity_frozen_before_statement_materialization") is True,
        "provider_calls_zero": manifest.get("provider_calls") == prereg.get("provider_calls") == 0,
        "task_content_inspected_false": manifest.get("task_content_inspected") is False,
        "mechanism_prereg_matches": manifest.get("mechanism_prereg_sha256") == prereg.get("prereg_sha256"),
        "prereg_current": prereg == current_prereg,
        "boundary_current": boundary == current_boundary,
    }
    ids = [str(row.get("instance_id", "")) for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    checks["unique_nonempty_ids"] = len(ids) == len(set(ids)) == 3 and all(ids)
    ready = all(checks.values())
    return {
        "ready": ready,
        "reason": "strict_v7_identity_certified" if ready else "strict_v7_identity_integrity_failed",
        "checks": checks,
        "instance_ids": ids,
        "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "prereg_file_sha256": hashlib.sha256(prereg_raw).hexdigest(),
        "boundary_file_sha256": hashlib.sha256(boundary_raw).hexdigest(),
    }


def run(output: Path = OUT) -> dict:
    certificate = certify_identity()
    if not certificate["ready"]:
        raise RuntimeError(certificate["reason"])
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    revision = manifest["source_revision"]
    rows = []
    for task in manifest["tasks"]:
        instance_id = task["instance_id"]
        task_root = ROOT_OUT / instance_id
        statement_path = task_root / "problem_statement.md"
        statement, statement_sha = fetch_statement_bounded(instance_id, revision, statement_path)
        statement_path.parent.mkdir(parents=True, exist_ok=True)
        statement_path.write_text(statement, encoding="utf-8")
        source = materialize_source(task, task_root / "source")
        if source["ready"]:
            try:
                base_bundle = build_bundle(
                    statement=statement,
                    workspace=task_root / "source",
                    base_commit=task["base_commit"],
                    forbidden_values=(instance_id, task["image"]),
                )
                plan = freeze_typed_plan(base_bundle["issue"], base_bundle["localization"])
                status = "supported"
                error = None
            except Exception as exc:
                base_bundle = None
                plan = None
                status = "unsupported"
                error = f"{type(exc).__name__}: {exc}"
        else:
            base_bundle = None
            plan = None
            status = "source_incomplete"
            error = None
        executable = int(plan.get("executable_candidate_count", 0)) if isinstance(plan, dict) else 0
        typed = int(plan.get("candidate_count", 0)) if isinstance(plan, dict) else 0
        rows.append(
            {
                "instance_id": instance_id,
                "statement_sha256": statement_sha,
                "statement_path": statement_path.relative_to(ROOT).as_posix(),
                "source": source,
                "projection_status": status,
                "projection_error": error,
                "typed_candidate_count": typed,
                "executable_candidate_count": executable,
                "plan": plan,
                "provider_calls": 0,
                "live_model_run": False,
                "forbidden_task_files_read": [],
            }
        )
    source_ready = sum(bool(row["source"]["ready"]) for row in rows)
    projection_supported = sum(row["projection_status"] == "supported" for row in rows)
    typed_tasks = sum(row["typed_candidate_count"] > 0 for row in rows)
    executable_tasks = sum(row["executable_candidate_count"] > 0 for row in rows)
    gate = executable_tasks >= 2 and source_ready == projection_supported == 3
    value = {
        "schema": "e1c-strict-v7-postfreeze-assessment-v1",
        "provider_calls": 0,
        "live_model_run": False,
        "identity_certificate": certificate,
        "source_ready_count": source_ready,
        "projection_supported_count": projection_supported,
        "typed_candidate_task_count": typed_tasks,
        "executable_candidate_task_count": executable_tasks,
        "minimum_executable_candidate_tasks": 2,
        "candidate_gate_passed": gate,
        "image_pull_allowed_by_candidate_gate": gate,
        "official_admission_allowed_by_candidate_gate": gate,
        "live_allowed": False,
        "reason": "ready_for_image_and_official_admission" if gate else "seal_pre_live_insufficient_executable_reproducers",
        "rows": rows,
    }
    value["summary_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


if __name__ == "__main__":
    result = run()
    print(json.dumps({
        "instance_ids": result["identity_certificate"]["instance_ids"],
        "source_ready_count": result["source_ready_count"],
        "projection_supported_count": result["projection_supported_count"],
        "typed_candidate_task_count": result["typed_candidate_task_count"],
        "executable_candidate_task_count": result["executable_candidate_task_count"],
        "candidate_gate_passed": result["candidate_gate_passed"],
        "reason": result["reason"],
        "provider_calls": result["provider_calls"],
        "summary_sha256": result["summary_sha256"],
    }, ensure_ascii=False, indent=2))
