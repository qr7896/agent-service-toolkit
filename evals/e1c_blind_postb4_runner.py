"""Post-B4 assertion-blind C0-C4 runner with real structured evidence and isolated grading."""

from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import json
import math
import subprocess
import sys
from functools import cache
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agents.model_budget import _prompt_text, budgeted_ainvoke
from agents.model_router import estimate_tokens
from core.settings import settings
from evals.e1b_editor_adapter import content_text, usage_tokens
from evals.e1c_admission import TASKS
from evals.e1c_blind_boundary import (
    assert_agent_payload,
    audit_serialized_agent_trace,
    build_agent_view,
    dump_agent_trace,
)
from evals.e1c_blind_evidence import (
    discover_test_roots,
    freeze_blind_evidence,
    lexical_windows,
)
from evals.e1c_blind_postb4_selector import canary_rows, frozen_selector_identity
from evals.e1c_blind_runtime import (
    build_runtime_view,
    freeze_probe_plan,
    inspect_candidate,
    repair_probe_context,
    run_prepatch_probes,
    verify_candidate,
)
from evals.e1c_live_runner import MANIFEST_SHA256, OUT, _patch, _save, _source
from evals.v3_compact_pilot import _apply_edits, _parse_edits
from schema.models import DeepseekModelName

RUN_ID = "e1c-blind-postb4-c4-v1"
PREP_ID = "e1c-blind-postb4-c4-prep-v1"
RUN_DIR = OUT / RUN_ID
PREP_DIR = OUT / PREP_ID
LEDGER = RUN_DIR / "provider_calls.jsonl"
MODEL = DeepseekModelName.DEEPSEEK_FLASH
CANARY_COUNT = 6
MAX_CALLS_PER_ARM = 2
MAX_OUTPUT_TOKENS = 900
TASK_TOKEN_CEILING = 9_000
TOTAL_TOKEN_CEILING = 108_000
PROMPT_RESERVE_CEILING = 7_000

SYSTEM = """You repair a Python repository using only the public issue and an assertion-blind exact-base evidence bundle.
Return JSON only and choose exactly one action:
{"inspect":{"path":"relative production .py path","symbol":"optional identifier"}}
or
{"edits":[{"path":"relative production .py path","old":"exact existing text","new":"replacement text"}]}.
Use at most four minimal exact replacements. Never edit tests. An inspect path must be one of candidate_paths.
Do not infer benchmark hidden tests, grader selectors, historical answers, or unshown files. If evidence is insufficient return {"edits":[]}.
"""

FINAL_SYSTEM = SYSTEM + """
This is the final repair request. Do not request another inspect; return edits or {"edits":[]}.
"""


def _statement_projection_path(instance_id: str) -> Path:
    return PREP_DIR / "agent" / instance_id / "problem_statement.md"


def _agent_bundle_path(instance_id: str) -> Path:
    return PREP_DIR / "agent" / instance_id / "bundle.json"


def _audit_prepatch_path(instance_id: str) -> Path:
    return PREP_DIR / "audit" / instance_id / "prepatch.json"


def _statement_from_task(instance_id: str) -> str:
    return (TASKS / instance_id / "problem_statement.md").read_text(encoding="utf-8")


def _selector_rows() -> list[dict]:
    rows = canary_rows(CANARY_COUNT)
    if len(rows) != CANARY_COUNT:
        raise ValueError("post-B4 selector did not produce six tasks")
    return rows


def _baseline_windows(statement: str, workspace: Path) -> list[dict]:
    return [
        {**item, "origin": "issue_lexical_baseline"}
        for item in lexical_windows(statement, workspace, limit=2)
    ]


def _trim_windows(windows: list[dict], *, limit: int) -> list[dict]:
    return [
        {
            **item,
            "text": item["text"][:1800],
        }
        for item in windows[:limit]
    ]


def _repair_payload(bundle: dict, *, arm: str, inspection: dict | None = None) -> dict:
    if arm == "baseline":
        windows = _trim_windows(bundle["baseline_windows"], limit=2)
        probe = {"status": "withheld_from_baseline"}
    elif arm == "treatment":
        windows = _trim_windows(bundle["structured_evidence"]["windows"], limit=5)
        probe = bundle["reproducer_context"]
    else:
        raise ValueError("unknown arm")
    payload = {
        "issue": bundle["problem_statement"],
        "source_commit": bundle["base_commit"],
        "evidence_mode": arm,
        "contract": bundle["structured_evidence"]["contract"] if arm == "treatment" else None,
        "reproducer": probe,
        "candidate_paths": list(dict.fromkeys(item["path"] for item in windows)),
        "excerpts": windows,
        "inspection": inspection,
    }
    assert_agent_payload(payload)
    encoded = json.dumps(payload, ensure_ascii=False)
    audit_serialized_agent_trace(encoded)
    return _fit(payload, final=inspection is not None)


def _reserve(payload: dict, *, final: bool) -> int:
    system = FINAL_SYSTEM if final else SYSTEM
    messages = [SystemMessage(content=system), HumanMessage(content=json.dumps(payload, ensure_ascii=False))]
    return math.ceil(estimate_tokens(_prompt_text(messages)) * 1.4) + MAX_OUTPUT_TOKENS


def _fit(payload: dict, *, final: bool) -> dict:
    value = {**payload, "excerpts": list(payload["excerpts"])}
    while len(value["excerpts"]) > 1 and _reserve(value, final=final) > PROMPT_RESERVE_CEILING:
        value["excerpts"].pop()
        value["candidate_paths"] = list(dict.fromkeys(item["path"] for item in value["excerpts"]))
    if _reserve(value, final=final) > PROMPT_RESERVE_CEILING:
        issue = value["issue"]
        value["issue"] = issue[:2600] + "\n[statement middle omitted by frozen budget rule]\n" + issue[-800:]
    if _reserve(value, final=final) > PROMPT_RESERVE_CEILING:
        value["reproducer"] = {"status": value["reproducer"].get("status", "no_reproducer")}
    if not value["excerpts"] or _reserve(value, final=final) > PROMPT_RESERVE_CEILING:
        raise ValueError("post-B4 payload does not fit frozen reserve ceiling")
    return value


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


def _config(task_arm: str, *, final: bool) -> dict:
    return {
        "configurable": {
            "provider_ledger_path": str(LEDGER),
            "provider_run_id": RUN_ID,
            "provider_task_id": task_arm,
            "provider_total_token_ceiling": TOTAL_TOKEN_CEILING,
            "provider_task_token_ceiling": TASK_TOKEN_CEILING,
            "provider_max_calls_per_task": MAX_CALLS_PER_ARM,
            "provider_max_output_tokens": MAX_OUTPUT_TOKENS,
            "provider_prompt_reserve_multiplier": 1.4,
            "provider_disable_thinking": True,
        }
    }


async def _call(task_arm: str, payload: dict, *, final: bool) -> tuple[str, dict]:
    system = FINAL_SYSTEM if final else SYSTEM
    response = await budgeted_ainvoke(
        _model(),
        [SystemMessage(content=system), HumanMessage(content=json.dumps(payload, ensure_ascii=False))],
        _config(task_arm, final=final),
        role="blind_postb4_editor",
    )
    return content_text(response), usage_tokens(response)


def _parse_action(raw: str, allowed_paths: set[str], *, allow_inspect: bool) -> tuple[str, object]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("model action must be a JSON object")
    if "inspect" in data:
        if not allow_inspect or set(data) != {"inspect"} or not isinstance(data["inspect"], dict):
            raise ValueError("invalid inspect action")
        path = data["inspect"].get("path")
        symbol = data["inspect"].get("symbol")
        if path not in allowed_paths or (symbol is not None and not isinstance(symbol, str)):
            raise ValueError("inspect path is not a frozen candidate")
        return "inspect", {"path": path, "symbol": symbol}
    edits = _parse_edits(raw, allowed_paths)
    return "edits", edits


def _workspace(row: dict, arm: str) -> Path:
    source = _source(row)
    workspace = RUN_DIR / "workspaces" / arm / row["instance_id"]
    if workspace.exists():
        raise FileExistsError(workspace)
    workspace.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-C", str(source), "worktree", "add", "--detach", str(workspace), row["base_commit"]],
        check=True,
        capture_output=True,
        timeout=120,
    )
    return workspace


def _validate_python_edits(workspace: Path, edits: list[dict]) -> None:
    for path in {edit["path"] for edit in edits}:
        source = (workspace / path).read_text(encoding="utf-8", errors="replace")
        ast.parse(source)


def _grade_isolated(instance_id: str, stage: str, patch: Path, evaluator_dir: Path) -> dict:
    command = [
        sys.executable,
        "-X",
        "utf8",
        "-m",
        "evals.e1c_docker_grade",
        instance_id,
        stage,
        str(patch.resolve()),
        str(evaluator_dir.resolve()),
    ]
    process = subprocess.run(command, capture_output=True, text=True, timeout=1800, check=False)
    if process.returncode != 0:
        raise RuntimeError(f"isolated grader failed: {process.stderr[-1200:]}")
    result_path = evaluator_dir / f"grade.{stage}.json"
    if not result_path.is_file():
        raise FileNotFoundError(result_path)
    return json.loads(result_path.read_text(encoding="utf-8"))


def static_preflight() -> dict:
    selector = frozen_selector_identity(CANARY_COUNT)
    rows = []
    for row in _selector_rows():
        source = _source(row)
        statement = _statement_from_task(row["instance_id"])
        view = build_runtime_view(row["instance_id"], statement, source)
        evidence = freeze_blind_evidence(statement, source)
        baseline = _baseline_windows(statement, source)
        plan = freeze_probe_plan(row, view)
        baseline_payload = _fit(
            {
                "issue": statement,
                "source_commit": row["base_commit"],
                "evidence_mode": "baseline",
                "contract": None,
                "reproducer": {"status": "withheld_from_baseline"},
                "candidate_paths": [item["path"] for item in baseline],
                "excerpts": _trim_windows(baseline, limit=2),
                "inspection": None,
            },
            final=False,
        )
        treatment_payload = _fit(
            {
                "issue": statement,
                "source_commit": row["base_commit"],
                "evidence_mode": "treatment",
                "contract": evidence["contract"],
                "reproducer": {"status": "no_reproducer"},
                "candidate_paths": [item["path"] for item in evidence["windows"][:5]],
                "excerpts": _trim_windows(evidence["windows"], limit=5),
                "inspection": None,
            },
            final=False,
        )
        image_ok = subprocess.run(
            ["docker", "image", "inspect", row["image"]],
            capture_output=True,
            check=False,
        ).returncode == 0
        rows.append(
            {
                "instance_id": row["instance_id"],
                "repo": row["repo"],
                "baseline_paths": baseline_payload["candidate_paths"],
                "treatment_paths": treatment_payload["candidate_paths"],
                "probe_count": len(plan["probes"]),
                "baseline_reserve": _reserve(baseline_payload, final=False),
                "treatment_reserve": _reserve(treatment_payload, final=False),
                "image_ready": image_ok,
                "ready": bool(baseline_payload["candidate_paths"])
                and bool(treatment_payload["candidate_paths"])
                and image_ok,
            }
        )
    return {
        "schema": "e1c-blind-postb4-static-preflight-v1",
        "run_id": RUN_ID,
        "prep_id": PREP_ID,
        "manifest_sha256": MANIFEST_SHA256,
        "selector": selector,
        "task_count": len(rows),
        "provider_calls": 0,
        "rows": rows,
        "prep_absent": not PREP_DIR.exists(),
        "run_absent": not RUN_DIR.exists(),
        "ready": len(rows) == CANARY_COUNT
        and all(row["ready"] for row in rows)
        and not PREP_DIR.exists()
        and not RUN_DIR.exists(),
    }


def prepare() -> dict:
    gate = static_preflight()
    if not gate["ready"]:
        raise RuntimeError(f"post-B4 static preflight not ready: {gate}")
    PREP_DIR.mkdir(parents=True, exist_ok=False)
    _save(PREP_DIR / "selector_identity.json", gate["selector"])
    _save(
        PREP_DIR / "identity.json",
        {
            **gate,
            "protocol": "e1c-blind-postb4-c0-c3-prep-v1",
            "provider_calls": 0,
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    )
    prepared = []
    for row in _selector_rows():
        instance_id = row["instance_id"]
        statement = _statement_from_task(instance_id)
        agent_dir = PREP_DIR / "agent" / instance_id
        audit_dir = PREP_DIR / "audit" / instance_id
        agent_dir.mkdir(parents=True)
        _statement_projection_path(instance_id).write_text(statement, encoding="utf-8")
        source = _source(row)
        view = build_runtime_view(instance_id, statement, source)
        evidence = freeze_blind_evidence(statement, source)
        baseline = _baseline_windows(statement, source)
        prepatch = run_prepatch_probes(row, view, audit_dir)
        bundle = {
            "schema": "e1c-blind-postb4-agent-bundle-v1",
            "instance_id": instance_id,
            "repo": row["repo"],
            "base_commit": row["base_commit"],
            "image": row["image"],
            "problem_statement": statement,
            "baseline_windows": baseline,
            "structured_evidence": evidence,
            "reproducer_context": repair_probe_context(prepatch),
            "probe_plan_sha256": prepatch["plan"]["plan_sha256"],
            "prepatch_freeze_sha256": prepatch["freeze_sha256"],
        }
        dump_agent_trace(bundle, _agent_bundle_path(instance_id))
        _save(_audit_prepatch_path(instance_id), prepatch)
        prepared.append(
            {
                "instance_id": instance_id,
                "reproducer_status": prepatch["reproducer_status"],
                "probe_count": len(prepatch["plan"]["probes"]),
                "bundle_sha256": hashlib.sha256(
                    _agent_bundle_path(instance_id).read_bytes()
                ).hexdigest(),
                "evidence_sha256": evidence["evidence_sha256"],
                "prepatch_freeze_sha256": prepatch["freeze_sha256"],
            }
        )
    result = {
        "schema": "e1c-blind-postb4-prepared-v1",
        "provider_calls": 0,
        "task_count": len(prepared),
        "rows": prepared,
        "ready": len(prepared) == CANARY_COUNT,
    }
    _save(PREP_DIR / "prepared.json", result)
    return result


def live_preflight() -> dict:
    if not PREP_DIR.is_dir():
        raise FileNotFoundError("post-B4 prep artifacts missing")
    prepared = json.loads((PREP_DIR / "prepared.json").read_text(encoding="utf-8"))
    selector = json.loads((PREP_DIR / "selector_identity.json").read_text(encoding="utf-8"))
    expected_selector = frozen_selector_identity(CANARY_COUNT)
    if selector["selector_sha256"] != expected_selector["selector_sha256"]:
        raise ValueError("selector identity changed after preparation")
    rows = []
    for row in _selector_rows():
        bundle = json.loads(_agent_bundle_path(row["instance_id"]).read_text(encoding="utf-8"))
        baseline = _repair_payload(bundle, arm="baseline")
        treatment = _repair_payload(bundle, arm="treatment")
        rows.append(
            {
                "instance_id": row["instance_id"],
                "baseline_reserve": _reserve(baseline, final=False),
                "treatment_reserve": _reserve(treatment, final=False),
                "ready": bool(baseline["candidate_paths"]) and bool(treatment["candidate_paths"]),
            }
        )
    return {
        "schema": "e1c-blind-postb4-live-preflight-v1",
        "run_id": RUN_ID,
        "selector_sha256": expected_selector["selector_sha256"],
        "prepared_ready": prepared.get("ready") is True,
        "provider_calls": 0,
        "run_absent": not RUN_DIR.exists(),
        "rows": rows,
        "ready": prepared.get("ready") is True
        and len(rows) == CANARY_COUNT
        and all(row["ready"] for row in rows)
        and not RUN_DIR.exists(),
    }


async def _arm(row: dict, arm: str) -> dict:
    instance_id = row["instance_id"]
    workspace = _workspace(row, arm)
    bundle = json.loads(_agent_bundle_path(instance_id).read_text(encoding="utf-8"))
    test_roots = discover_test_roots(workspace)
    view = build_agent_view(
        instance_id=instance_id,
        problem_statement=bundle["problem_statement"],
        workspace=workspace,
        original_test_roots=test_roots,
    )
    repair_dir = RUN_DIR / "repair" / arm / instance_id
    evaluator_dir = RUN_DIR / "evaluator" / arm / instance_id
    repair_dir.mkdir(parents=True)
    payload = _repair_payload(bundle, arm=arm)
    dump_agent_trace(payload, repair_dir / "payload.first.json")
    task_arm = f"{instance_id}:{arm}"
    raw, first_usage = await _call(task_arm, payload, final=False)
    (repair_dir / "response.first.txt").write_text(raw, encoding="utf-8")
    allowed = set(payload["candidate_paths"])
    try:
        action, value = _parse_action(raw, allowed, allow_inspect=True)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        return {
            "instance_id": instance_id,
            "arm": arm,
            "resolved": False,
            "status": "invalid_action",
            "model_calls": 1,
            "first_usage": first_usage,
            "error": f"{type(exc).__name__}: {exc}",
        }
    usages = [first_usage]
    if action == "inspect":
        inspect_request = value
        inspection = inspect_candidate(view, inspect_request["path"], inspect_request["symbol"])
        payload = _repair_payload(bundle, arm=arm, inspection=inspection)
        dump_agent_trace(payload, repair_dir / "payload.final.json")
        raw, second_usage = await _call(task_arm, payload, final=True)
        usages.append(second_usage)
        (repair_dir / "response.final.txt").write_text(raw, encoding="utf-8")
        try:
            action, value = _parse_action(raw, set(payload["candidate_paths"]), allow_inspect=False)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            return {
                "instance_id": instance_id,
                "arm": arm,
                "resolved": False,
                "status": "invalid_final_action",
                "model_calls": 2,
                "usages": usages,
                "error": f"{type(exc).__name__}: {exc}",
            }
    edits = value
    if action != "edits" or not edits:
        return {
            "instance_id": instance_id,
            "arm": arm,
            "resolved": False,
            "status": "abstain",
            "model_calls": len(usages),
            "usages": usages,
        }
    try:
        _apply_edits(workspace, edits)
        _validate_python_edits(workspace, edits)
        patch = repair_dir / "candidate.diff"
        _patch(workspace, patch)
        if not patch.stat().st_size:
            raise ValueError("empty candidate patch")
    except (OSError, PermissionError, SyntaxError, TypeError, ValueError) as exc:
        return {
            "instance_id": instance_id,
            "arm": arm,
            "resolved": False,
            "status": "patch_rejected",
            "model_calls": len(usages),
            "usages": usages,
            "error": f"{type(exc).__name__}: {exc}",
        }
    candidate_sha = hashlib.sha256(patch.read_bytes()).hexdigest()
    frozen = {
        "instance_id": instance_id,
        "arm": arm,
        "candidate_patch_sha256": candidate_sha,
        "model_calls": len(usages),
        "usages": usages,
    }
    _save(repair_dir / "candidate.freeze.json", frozen)
    prepatch = json.loads(_audit_prepatch_path(instance_id).read_text(encoding="utf-8"))
    verification = verify_candidate(row, prepatch, patch, repair_dir / "verification")
    _save(repair_dir / "verification.json", verification)
    if not verification["passed"]:
        return {
            **frozen,
            "resolved": False,
            "status": "blind_verification_failed",
            "verification_reasons": verification["reasons"],
        }
    stage = f"postb4_{arm}"
    grade_result = _grade_isolated(instance_id, stage, patch, evaluator_dir)
    return {
        **frozen,
        "resolved": bool(grade_result["resolved"]),
        "status": "graded",
        "grade_valid_log": bool(grade_result["valid_log"]),
        "grade_exit_code": grade_result["exit_code"],
    }


def _summary(rows: list[dict]) -> dict:
    baseline = {row["instance_id"] for row in rows if row["arm"] == "baseline" and row["resolved"]}
    treatment = {row["instance_id"] for row in rows if row["arm"] == "treatment" and row["resolved"]}
    provider_tokens = sum(
        usage.get("total_tokens", 0)
        for row in rows
        for usage in row.get("usages", ([row["first_usage"]] if "first_usage" in row else []))
    )
    return {
        "schema": "e1c-blind-postb4-c4-result-v1",
        "rows": rows,
        "baseline_resolved": len(baseline),
        "treatment_resolved": len(treatment),
        "treatment_only_resolved": sorted(treatment - baseline),
        "baseline_only_resolved": sorted(baseline - treatment),
        "net_new_resolved": len(treatment - baseline),
        "provider_tokens": provider_tokens,
        "expand_c5": bool(treatment - baseline) and not (baseline - treatment),
    }


async def run_canary() -> dict:
    gate = live_preflight()
    if not gate["ready"]:
        raise RuntimeError(f"post-B4 live preflight not ready: {gate}")
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    identity = {
        **gate,
        "protocol": "e1c-blind-postb4-c4-v1",
        "model": str(MODEL),
        "system_sha256": hashlib.sha256(SYSTEM.encode()).hexdigest(),
        "final_system_sha256": hashlib.sha256(FINAL_SYSTEM.encode()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "max_calls_per_arm": MAX_CALLS_PER_ARM,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "task_token_ceiling": TASK_TOKEN_CEILING,
        "total_token_ceiling": TOTAL_TOKEN_CEILING,
        "stop_rule": "C5 only if >=1 treatment-only official resolved, 0 baseline-only resolved, and no safety/budget anomaly",
    }
    _save(RUN_DIR / "identity.json", identity)
    outcomes = []
    for row in _selector_rows():
        for arm in ("baseline", "treatment"):
            try:
                outcome = await _arm(row, arm)
            except Exception as exc:
                state = {
                    "schema": "e1c-blind-postb4-c4-state-v1",
                    "rows": outcomes,
                    "status": "interrupted_no_auto_retry",
                    "interrupted": f"{row['instance_id']}:{arm}",
                    "error": f"{type(exc).__name__}: {exc}",
                }
                _save(RUN_DIR / "state.json", state)
                raise
            outcomes.append(outcome)
            _save(RUN_DIR / "state.json", {"schema": "e1c-blind-postb4-c4-state-v1", "rows": outcomes})
    summary = _summary(outcomes)
    _save(RUN_DIR / "result.json", summary)
    return summary


def c5_gate() -> dict:
    result_path = RUN_DIR / "result.json"
    if not result_path.is_file():
        return {"schema": "e1c-blind-postb4-c5-gate-v1", "ready": False, "reason": "C4_not_run"}
    result = json.loads(result_path.read_text(encoding="utf-8"))
    return {
        "schema": "e1c-blind-postb4-c5-gate-v1",
        "ready": result.get("expand_c5") is True,
        "reason": "C4_passed" if result.get("expand_c5") is True else "C4_stop_rule_not_met",
        "c4_result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("preflight", "prepare", "live-preflight", "run-canary", "c5-gate"),
    )
    args = parser.parse_args()
    if args.command == "preflight":
        result = static_preflight()
    elif args.command == "prepare":
        result = prepare()
    elif args.command == "live-preflight":
        result = live_preflight()
    elif args.command == "run-canary":
        result = asyncio.run(run_canary())
    else:
        result = c5_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.command in {"preflight", "live-preflight"} and not result["ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
