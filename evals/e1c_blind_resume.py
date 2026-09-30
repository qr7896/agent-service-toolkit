"""Resume an interrupted blind B4 canary without replaying completed provider calls."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from evals.e1c_blind_runner import (
    RUN_DIR,
    RUN_ID,
    SYSTEM,
    _arm,
    _canary_rows,
)
from evals.e1c_docker_grade import grade
from evals.e1c_live_runner import _save
from evals.v3_compact_pilot import _parse_edits

LEDGER = RUN_DIR / "provider_calls.jsonl"


def _ledger_completed() -> dict[str, dict]:
    if not LEDGER.is_file():
        return {}
    completed: dict[str, dict] = {}
    started: set[str] = set()
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        task_id = row.get("task_id")
        if row.get("run_id") != RUN_ID or not task_id:
            continue
        if row.get("status") == "started":
            started.add(task_id)
        elif row.get("status") == "completed":
            if task_id in completed:
                raise ValueError(f"duplicate completed provider call: {task_id}")
            completed[task_id] = row
    if not set(completed) <= started:
        raise ValueError("completed provider call without matching started ledger row")
    return completed


def _usage(ledger_row: dict) -> dict:
    return {
        key: ledger_row[key]
        for key in ("input_tokens", "output_tokens", "total_tokens")
        if key in ledger_row
    }


def _existing_outcome(row: dict, arm: str, ledger_row: dict) -> dict:
    instance_id = row["instance_id"]
    repair_dir = RUN_DIR / "repair" / arm / instance_id
    evaluator_dir = RUN_DIR / "evaluator" / arm / instance_id
    payload_path = repair_dir / "payload.json"
    response_path = repair_dir / "response.txt"
    if not payload_path.is_file() or not response_path.is_file():
        raise FileNotFoundError(f"completed call missing repair artifacts: {instance_id}:{arm}")
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    raw = response_path.read_text(encoding="utf-8")
    patch = repair_dir / "candidate.diff"
    usage = _usage(ledger_row)
    if patch.is_file() and patch.stat().st_size:
        result_path = evaluator_dir / f"grade.{arm}.json"
        result = (
            json.loads(result_path.read_text(encoding="utf-8"))
            if result_path.is_file()
            else grade(instance_id, arm, patch, evaluator_dir)
        )
        return {
            "instance_id": instance_id,
            "arm": arm,
            "resolved": bool(result["resolved"]),
            "abstain": False,
            "usage": usage,
            "resumed_from_completed_call": True,
        }
    try:
        edits = _parse_edits(raw, {item["path"] for item in payload["excerpts"]})
    except (json.JSONDecodeError, TypeError, ValueError, PermissionError, OSError) as exc:
        return {
            "instance_id": instance_id,
            "arm": arm,
            "resolved": False,
            "patch_failure": f"{type(exc).__name__}: {exc}",
            "usage": usage,
            "resumed_from_completed_call": True,
        }
    if edits:
        raise ValueError(f"completed edit call missing candidate patch: {instance_id}:{arm}")
    return {
        "instance_id": instance_id,
        "arm": arm,
        "resolved": False,
        "abstain": True,
        "usage": usage,
        "resumed_from_completed_call": True,
    }


def _summary(outcomes: list[dict]) -> dict:
    baseline = {r["instance_id"] for r in outcomes if r["arm"] == "baseline" and r["resolved"]}
    structured = {r["instance_id"] for r in outcomes if r["arm"] == "structured" and r["resolved"]}
    return {
        "schema": "e1c-blind-canary-result-v1",
        "rows": outcomes,
        "baseline_resolved": len(baseline),
        "structured_resolved": len(structured),
        "net_new_resolved": len(structured - baseline),
        "lost_resolved": len(baseline - structured),
        "expand_b5": bool(structured - baseline) and not (baseline - structured),
    }


def preflight() -> dict:
    identity_path = RUN_DIR / "identity.json"
    if not identity_path.is_file():
        raise FileNotFoundError("blind canary identity missing")
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    if identity["run_id"] != RUN_ID:
        raise ValueError("blind canary run identity mismatch")
    if identity["system_sha256"] != hashlib.sha256(SYSTEM.encode()).hexdigest():
        raise ValueError("blind canary system prompt changed")
    completed = _ledger_completed()
    planned = [f"{row['instance_id']}:{arm}" for row in _canary_rows() for arm in ("baseline", "structured")]
    unknown = sorted(set(completed) - set(planned))
    if unknown:
        raise ValueError(f"unexpected completed provider task ids: {unknown}")
    return {
        "schema": "e1c-blind-canary-resume-preflight-v1",
        "run_id": RUN_ID,
        "planned_calls": len(planned),
        "completed_calls": len(completed),
        "remaining_calls": len(planned) - len(completed),
        "completed_task_ids": sorted(completed),
        "ready": len(completed) <= len(planned),
    }


async def run() -> dict:
    gate = preflight()
    if not gate["ready"]:
        raise RuntimeError(f"resume preflight failed: {gate}")
    completed = _ledger_completed()
    _save(
        RUN_DIR / "resume_identity.json",
        {
            **gate,
            "protocol": "e1c-assertion-blind-canary-resume-v1",
            "resume_runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "no_replay_rule": "completed provider task_ids are reconstructed or evaluator-graded, never reinvoked",
        },
    )
    outcomes: list[dict] = []
    for row in _canary_rows():
        for arm in ("baseline", "structured"):
            task_id = f"{row['instance_id']}:{arm}"
            if task_id in completed:
                outcome = _existing_outcome(row, arm, completed[task_id])
            else:
                outcome = await _arm(row, arm)
            outcomes.append(outcome)
            _save(
                RUN_DIR / "state.json",
                {
                    "schema": "e1c-blind-canary-state-v1",
                    "resume_protocol": "e1c-assertion-blind-canary-resume-v1",
                    "rows": outcomes,
                },
            )
    summary = _summary(outcomes)
    _save(RUN_DIR / "result.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run"))
    args = parser.parse_args()
    result = preflight() if args.command == "preflight" else asyncio.run(run())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
