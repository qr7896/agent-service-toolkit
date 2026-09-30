"""Read-only reconciliation for the post-outcome E1-C DEV v2 run."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from evals.e1c_dev_v2 import (
    LEDGER,
    RUN_DIR,
    RUN_ID,
    STATE,
    TASK_TOKEN_CEILING,
    TOTAL_TOKEN_CEILING,
    _manifest,
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict:
    problems = []
    identity, state = _read(RUN_DIR / "identity.json"), _read(STATE)
    ids = [item["instance_id"] for item in _manifest()["tasks"]]
    rows = state["rows"]
    if (identity["run_id"] != RUN_ID or state.get("status") != "completed"
            or state["run_id"] != RUN_ID or [row["instance_id"] for row in rows] != ids):
        problems.append("incomplete_or_out_of_order_denominator")
    if identity["runner_sha256"] != _sha(Path(__file__).with_name("e1c_dev_v2.py")):
        problems.append("runner_changed_since_live")
    if identity["evidence_sha256"] != _sha(Path(__file__).with_name("e1c_evidence_v2.py")):
        problems.append("evidence_changed_since_live")
    latest = {}
    started = set()
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        call_id = event.get("call_id")
        if event.get("run_id") != RUN_ID or not call_id:
            problems.append("foreign_or_unidentified_provider_event")
            continue
        if event.get("status") == "started":
            if call_id in started:
                problems.append(f"duplicate_call_start:{call_id}")
            started.add(call_id)
        latest[call_id] = event
    if len(started) != len(latest) or any(event.get("status") != "completed" for event in latest.values()):
        problems.append("provider_call_unresolved_or_failed")
    completed = [event for event in latest.values() if event.get("status") == "completed"]
    by_task = defaultdict(list)
    for event in completed:
        by_task[event["task_id"]].append(event)
    tokens = sum(int(event["total_tokens"]) for event in completed)
    if tokens > TOTAL_TOKEN_CEILING or set(by_task) != set(ids):
        problems.append("global_budget_or_task_set_mismatch")
    noops = 0
    patch_failures = 0
    official_grades = 0
    critical_safety = 0
    infrastructure = 0
    for row in rows:
        instance_id = row["instance_id"]
        calls = by_task.get(instance_id, [])
        used = sum(int(event["total_tokens"]) for event in calls)
        reported = row["first_usage"]["total_tokens"] + row.get("final_usage", {}).get("total_tokens", 0)
        if len(calls) != row["model_calls"] or len(calls) > 2 or used != reported or used > TASK_TOKEN_CEILING:
            problems.append(f"{instance_id}:provider_budget_or_call_mismatch")
        artifacts = RUN_DIR / "artifacts" / instance_id
        for stage in ("first", "final") if row["model_calls"] == 2 else ("first",):
            grade = row[f"{stage}_grade"]
            if not (artifacts / f"payload.{stage}.json").is_file() or not (artifacts / f"response.{stage}.txt").is_file():
                problems.append(f"{instance_id}:{stage}:missing_payload_or_response")
            if grade.get("schema") == "e1c-dev-v2-noop":
                noops += 1
                if (artifacts / f"grade.{stage}.json").exists():
                    problems.append(f"{instance_id}:{stage}:noop_was_graded")
            elif grade.get("schema") == "e1c-docker-grade-v2":
                official_grades += 1
                patch_path = artifacts / f"patch.{stage}.diff"
                log_path = artifacts / f"grade.{stage}.log"
                if not patch_path.is_file() or not log_path.is_file() or not (artifacts / f"grade.{stage}.json").is_file():
                    problems.append(f"{instance_id}:{stage}:missing_grade_artifact")
                elif (_sha(patch_path) != grade["candidate_patch_sha256"]
                      or _sha(log_path) != grade["log_sha256"]
                      or _read(artifacts / f"grade.{stage}.json") != grade):
                    problems.append(f"{instance_id}:{stage}:grade_hash_mismatch")
                critical_safety += not grade["source_identity_valid"]
                infrastructure += grade["timeout"] or not grade["valid_log"]
            elif grade.get("guard_output_tail", "").startswith("patch_failure:"):
                patch_failures += 1
            else:
                problems.append(f"{instance_id}:{stage}:unknown_grade_type")
        expected = row.get("final_grade", row["first_grade"])["resolved"]
        if row["resolved"] != expected or row["first_resolved"] != row["first_grade"]["resolved"]:
            problems.append(f"{instance_id}:outcome_mismatch")
    return {
        "schema": "e1c-dev-v2-audit", "run_id": RUN_ID, "denominator": len(ids),
        "rows": len(rows), "first_pass_resolved": sum(bool(row["first_resolved"]) for row in rows),
        "final_resolved": sum(bool(row["resolved"]) for row in rows),
        "provider_calls_completed": len(completed), "provider_tokens": tokens,
        "noop_stages": noops, "patch_failure_stages": patch_failures,
        "official_grade_stages": official_grades, "infrastructure_failures": infrastructure,
        "critical_safety_violations": critical_safety,
        "artifact_completeness": not problems, "problems": problems,
        "claim_boundary": "post-outcome repeated 30-task DEV; not independent E1-C or E2 efficacy",
    }


def main() -> None:
    result = audit()
    (RUN_DIR / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["problems"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
