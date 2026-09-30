"""One-shot E1-C live runner; ``preflight`` never calls a model."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
from functools import cache
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agents.model_budget import budgeted_ainvoke
from core.settings import settings
from evals.e1b_editor_adapter import content_text, usage_tokens
from evals.e1c_admission import ROOT
from evals.e1c_docker_grade import grade
from evals.e1c_live_preflight import check, fit_payload, payload
from evals.v3_compact_pilot import (
    SYSTEM,
    _apply_edits,
    _classify_failure,
    _escalation_card,
    _escalation_policy,
    _parse_edits,
)
from schema.models import DeepseekModelName

OUT = ROOT / ".codex" / "e1c"
MANIFEST = OUT / "final_admitted_manifest.json"
MANIFEST_SHA256 = "7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435"
RUN_ID = "e1c-n30-7d8e6569"
RUN_DIR = OUT / RUN_ID
LEDGER = RUN_DIR / "provider_calls.jsonl"
STATE = RUN_DIR / "state.json"
MODEL = DeepseekModelName.DEEPSEEK_FLASH
TOTAL_TOKEN_CEILING = 120_000
TASK_TOKEN_CEILING = 4_000


def _manifest() -> dict:
    data = MANIFEST.read_bytes()
    if hashlib.sha256(data).hexdigest() != MANIFEST_SHA256:
        raise ValueError("final cohort hash differs from frozen identity")
    manifest = json.loads(data)
    ids = [row["instance_id"] for row in manifest["tasks"]]
    if (manifest["schema"] != "e1c-final-admitted-cohort-v1"
            or manifest["status"] != "admitted_pre_live"
            or manifest["count"] != 30 or len(ids) != 30 or len(set(ids)) != 30
            or any(not row["admitted"] for row in manifest["tasks"])):
        raise ValueError("invalid frozen admitted cohort")
    return manifest


def preflight() -> dict:
    manifest = _manifest()
    result = check(MANIFEST)
    for row in manifest["tasks"]:
        instance_id = row["instance_id"]
        _source(row)
        admission = OUT / "admission_v2" / instance_id
        base = json.loads((admission / "base.json").read_text(encoding="utf-8"))
        gold = json.loads((admission / "gold.json").read_text(encoding="utf-8"))
        if not (base["phase_pass"] and gold["phase_pass"]):
            raise ValueError(f"admission changed: {instance_id}")
        digest = subprocess.check_output(
            ["docker", "image", "inspect", base["image"], "--format", "{{index .RepoDigests 0}}"],
            text=True,
        ).strip()
        if digest != base["image_digest"] or digest != gold["image_digest"]:
            raise ValueError(f"admitted image digest changed: {instance_id}")
    return {
        "schema": "e1c-live-runner-preflight-v1",
        "run_id": RUN_ID,
        "manifest_sha256": MANIFEST_SHA256,
        "model": str(MODEL),
        "task_count": len(manifest["tasks"]),
        "ready_count": result["ready_count"],
        "max_first_reserve": result["max_first_reserve"],
        "max_escalation_reserve_proxy": result["max_escalation_reserve_proxy"],
        "provider_calls": 0,
        "artifacts_absent": not RUN_DIR.exists(),
        "ready": result["ready_count"] == 30 and not RUN_DIR.exists(),
    }


def _save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _source(row: dict) -> Path:
    source = OUT / "repos" / row["repo"].replace("/", "__") / row["base_commit"]
    if not source.is_dir():
        raise FileNotFoundError(source)
    head = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if head != row["base_commit"]:
        raise ValueError(f"source HEAD changed: {row['instance_id']}")
    if subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"]):
        raise ValueError(f"source checkout is dirty: {row['instance_id']}")
    return source


def _workspace(row: dict) -> Path:
    source = _source(row)
    workspace = RUN_DIR / "workspaces" / row["instance_id"]
    if workspace.exists():
        raise FileExistsError(workspace)
    workspace.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-C", str(source), "worktree", "add", "--detach", str(workspace), row["base_commit"]],
        check=True, capture_output=True, timeout=120,
    )
    return workspace


def _patch(workspace: Path, path: Path) -> None:
    data = subprocess.check_output(
        ["git", "-C", str(workspace), "diff", "--binary", "--no-ext-diff"], timeout=120
    )
    path.write_bytes(data)


def _config(instance_id: str, *, escalation: bool = False) -> dict:
    return {"configurable": {
        "provider_ledger_path": str(LEDGER),
        "provider_run_id": RUN_ID,
        "provider_task_id": instance_id,
        "provider_total_token_ceiling": TOTAL_TOKEN_CEILING,
        "provider_task_token_ceiling": TASK_TOKEN_CEILING,
        "provider_max_calls_per_task": 2,
        "provider_max_output_tokens": 400 if escalation else 600,
        "provider_prompt_reserve_multiplier": 1.0 if escalation else 2.0,
        "provider_disable_thinking": True,
    }}


@cache
def _model() -> ChatOpenAI:
    return ChatOpenAI(
        model=str(MODEL),
        temperature=0.5,
        streaming=True,
        openai_api_base="https://api.deepseek.com",
        openai_api_key=settings.DEEPSEEK_API_KEY,
        max_retries=0,
    )


async def _call(instance_id: str, value: dict, *, escalation: bool = False) -> tuple[str, dict]:
    response = await budgeted_ainvoke(
        _model(),
        [SystemMessage(content=SYSTEM), HumanMessage(content=json.dumps(value, ensure_ascii=False))],
        _config(instance_id, escalation=escalation),
        role="compact_editor",
    )
    return content_text(response), usage_tokens(response)


def _attempt(instance_id: str, workspace: Path, raw: str, value: dict, stage: str, artifacts: Path) -> tuple[dict, str | None]:
    (artifacts / f"response.{stage}.txt").write_text(raw, encoding="utf-8")
    try:
        edits = _parse_edits(raw, {item["path"] for item in value["excerpts"]})
        _apply_edits(workspace, edits)
        _patch(workspace, artifacts / f"patch.{stage}.diff")
    except (json.JSONDecodeError, TypeError, ValueError, PermissionError, OSError) as exc:
        failure = f"patch_failure:{type(exc).__name__}:{exc}"
        return {"resolved": False, "guard_output_tail": failure}, failure
    return grade(instance_id, stage, artifacts / f"patch.{stage}.diff", artifacts), None


async def _task(row: dict) -> dict:
    instance_id = row["instance_id"]
    workspace = _workspace(row)
    artifacts = RUN_DIR / "artifacts" / instance_id
    artifacts.mkdir(parents=True)
    first_value = fit_payload(payload(
        instance_id, workspace, row["base_commit"]
    ))
    _save(artifacts / "payload.first.json", first_value)
    first_raw, first_usage = await _call(instance_id, first_value)
    first, failure = _attempt(instance_id, workspace, first_raw, first_value, "first", artifacts)
    classification = _classify_failure(
        {"passed": first["resolved"], "stdout": first.get("guard_output_tail", "")}, failure
    )
    policy = _escalation_policy(classification)
    result = {
        "instance_id": instance_id,
        "first_resolved": first["resolved"],
        "resolved": first["resolved"],
        "failure_class": classification,
        "escalation_policy": policy,
        "model_calls": 1,
        "first_usage": first_usage,
        "first_grade": first,
    }
    if not first["resolved"] and policy != "stop":
        value = fit_payload(payload(instance_id, workspace, row["base_commit"]))
        value["escalation"] = {
            "policy": policy,
            "evidence": _escalation_card(
                classification,
                {"stdout": first.get("guard_output_tail", ""), "stderr": ""},
            ),
        }
        _save(artifacts / "payload.final.json", value)
        raw, usage = await _call(instance_id, value, escalation=True)
        final, final_failure = _attempt(instance_id, workspace, raw, value, "final", artifacts)
        result.update({
            "resolved": final["resolved"],
            "model_calls": 2,
            "final_usage": usage,
            "final_grade": final,
            "final_failure": final_failure,
        })
    return result


async def run() -> dict:
    gate = preflight()
    if not gate["ready"]:
        raise RuntimeError(f"E1-C live preflight not ready: {gate}")
    manifest = _manifest()
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    _save(RUN_DIR / "identity.json", {
        **gate,
        "protocol": "e1c-n30-live-v1",
        "task_token_ceiling": TASK_TOKEN_CEILING,
        "total_token_ceiling": TOTAL_TOKEN_CEILING,
        "max_calls_per_task": 2,
        "system_sha256": hashlib.sha256(SYSTEM.encode()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    })
    state = {"schema": "e1c-n30-live-state-v1", "run_id": RUN_ID, "rows": []}
    for row in manifest["tasks"]:
        try:
            outcome = await _task(row)
        except Exception as exc:
            state["stop_reason"] = "task_interrupted_no_auto_retry"
            state["interrupted_task"] = row["instance_id"]
            state["error"] = f"{type(exc).__name__}: {exc}"
            _save(STATE, state)
            raise
        state["rows"].append(outcome)
        _save(STATE, state)
        print(json.dumps({"instance_id": row["instance_id"], "resolved": outcome["resolved"]}), flush=True)
    state["status"] = "completed"
    _save(STATE, state)
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run"))
    args = parser.parse_args()
    result = preflight() if args.command == "preflight" else asyncio.run(run())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.command == "preflight" and not result["ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
