"""Read-only E1-C n=30 artifact and provider-ledger audit."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from evals.e1c_live_runner import (
    LEDGER,
    MANIFEST,
    MANIFEST_SHA256,
    RUN_DIR,
    RUN_ID,
    STATE,
    TASK_TOKEN_CEILING,
    TOTAL_TOKEN_CEILING,
    _parse_edits,
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stage(instance_id: str, row: dict, stage: str, problems: list[str]) -> bool:
    root = RUN_DIR / "artifacts" / instance_id
    grade = row[f"{stage}_grade"]
    payload_path, response_path = root / f"payload.{stage}.json", root / f"response.{stage}.txt"
    if not payload_path.is_file() or not response_path.is_file():
        problems.append(f"{instance_id}:{stage}:missing_payload_or_response")
        return False
    if grade.get("schema") != "e1c-docker-grade-v2":
        if not grade.get("guard_output_tail", "").startswith("patch_failure:"):
            problems.append(f"{instance_id}:{stage}:missing_grade_without_patch_failure")
        return False
    grade_path, log_path, patch_path = (
        root / f"grade.{stage}.json", root / f"grade.{stage}.log", root / f"patch.{stage}.diff"
    )
    if not all(path.is_file() for path in (grade_path, log_path, patch_path)):
        problems.append(f"{instance_id}:{stage}:missing_grade_artifacts")
        return False
    if _json(grade_path) != grade or _sha(log_path) != grade["log_sha256"] or _sha(patch_path) != grade["candidate_patch_sha256"]:
        problems.append(f"{instance_id}:{stage}:artifact_hash_or_content_mismatch")
    try:
        value = _json(payload_path)
        _parse_edits(response_path.read_text(encoding="utf-8"), {item["path"] for item in value["excerpts"]})
    except (ValueError, TypeError, PermissionError, KeyError) as exc:
        problems.append(f"{instance_id}:{stage}:guard_replay_failed:{type(exc).__name__}")
    if grade["instance_id"] != instance_id or grade["stage"] != stage:
        problems.append(f"{instance_id}:{stage}:grade_identity_mismatch")
    if not grade["source_identity_valid"]:
        problems.append(f"{instance_id}:{stage}:source_identity_violation")
    return bool(grade["timeout"] or not grade["valid_log"] or not grade["source_identity_valid"])


def audit() -> dict:
    problems: list[str] = []
    manifest, identity, state = _json(MANIFEST), _json(RUN_DIR / "identity.json"), _json(STATE)
    ids = [item["instance_id"] for item in manifest["tasks"]]
    rows = state["rows"]
    if _sha(MANIFEST) != MANIFEST_SHA256 or identity["manifest_sha256"] != MANIFEST_SHA256:
        problems.append("manifest_identity_mismatch")
    if identity["runner_sha256"] != _sha(Path(__file__).with_name("e1c_live_runner.py")):
        problems.append("runner_changed_since_live")
    if state.get("status") != "completed" or state["run_id"] != RUN_ID or [row["instance_id"] for row in rows] != ids:
        problems.append("incomplete_or_out_of_order_denominator")
    latest: dict[str, dict] = {}
    started: set[str] = set()
    completed_ids: set[str] = set()
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            problems.append("malformed_provider_ledger_line")
            continue
        if event.get("run_id") != RUN_ID or not event.get("call_id"):
            problems.append("foreign_or_unidentified_provider_event")
            continue
        call_id = event["call_id"]
        if event["status"] == "started":
            if call_id in started:
                problems.append(f"duplicate_call_start:{call_id}")
            started.add(call_id)
        elif event["status"] == "completed":
            if call_id in completed_ids:
                problems.append(f"duplicate_call_completion:{call_id}")
            completed_ids.add(call_id)
        latest[call_id] = event
    completed = [event for event in latest.values() if event.get("status") == "completed"]
    if len(started) != len(latest) or len(completed) != len(latest):
        problems.append("provider_call_unresolved_or_failed")
    by_task: dict[str, list[dict]] = defaultdict(list)
    for event in completed:
        by_task[event["task_id"]].append(event)
    tokens = sum(int(event["total_tokens"]) for event in completed)
    if tokens > TOTAL_TOKEN_CEILING:
        problems.append("global_token_budget_exceeded")
    infra_tasks = set()
    for row in rows:
        instance_id = row["instance_id"]
        calls = by_task.get(instance_id, [])
        if len(calls) != row["model_calls"] or len(calls) > 2:
            problems.append(f"{instance_id}:provider_call_count_mismatch")
        used = sum(int(event["total_tokens"]) for event in calls)
        reported = row["first_usage"]["total_tokens"] + row.get("final_usage", {}).get("total_tokens", 0)
        if used != reported or used > TASK_TOKEN_CEILING:
            problems.append(f"{instance_id}:provider_token_mismatch_or_budget_exceeded")
        if _stage(instance_id, row, "first", problems):
            infra_tasks.add(instance_id)
        if row["model_calls"] == 2 and _stage(instance_id, row, "final", problems):
            infra_tasks.add(instance_id)
        expected = row.get("final_grade", row["first_grade"])["resolved"]
        if row["resolved"] != expected or row["first_resolved"] != row["first_grade"]["resolved"]:
            problems.append(f"{instance_id}:outcome_mismatch")
    if set(by_task) != set(ids):
        problems.append("provider_task_set_mismatch")
    gate = "PASS" if not problems and len(infra_tasks) <= 3 else "BLOCKED"
    blocked_writes = sum(
        "patch_failure:PermissionError" in row[stage].get("guard_output_tail", "")
        for row in rows for stage in ("first_grade", "final_grade") if stage in row
    )
    return {
        "schema": "e1c-n30-live-audit-v1",
        "run_id": RUN_ID,
        "denominator": len(ids),
        "rows": len(rows),
        "first_pass_resolved": sum(bool(row["first_resolved"]) for row in rows),
        "final_resolved": sum(bool(row["resolved"]) for row in rows),
        "selective_salvage": sum(bool(row["resolved"] and not row["first_resolved"]) for row in rows),
        "provider_calls_completed": len(completed),
        "provider_tokens": tokens,
        "infrastructure_failure_tasks": len(infra_tasks),
        "blocked_unsafe_write_attempts": blocked_writes,
        "critical_safety_violations": sum(
            "guard_replay_failed" in issue or "source_identity_violation" in issue
            for issue in problems
        ),
        "artifact_completeness": len(problems) == 0,
        "e2_entry_gate": gate,
        "problems": problems,
        "claim_boundary": "E1-C operational validation only; not pooled with Formal E1 n=30",
    }


def main() -> None:
    result = audit()
    (RUN_DIR / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["problems"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
