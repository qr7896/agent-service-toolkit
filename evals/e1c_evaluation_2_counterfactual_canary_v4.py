"""Independent counterfactual canary: fixed three tasks, Flash at most 60k tokens."""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import subprocess
import urllib.request

import httpx

from evals import e1c_evaluation_2_counterfactual_dev as cf
from evals import e1c_evaluation_2_hybrid_canary_v3 as frame
from evals.e1c_evaluation_2_contract_method import parse_response
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_source_contract import source_trees

OUT = ROOT / ".codex/e1c/evaluation_2/counterfactual-canary-v4"
FREEZE = ROOT / "data/e1c_evaluation_2_counterfactual_canary_v4_method_freeze.json"
IDENTITY = ROOT / "data/e1c_evaluation_2_counterfactual_canary_v4_identity.json"
PROTOCOL = ROOT / "docs/research/E1C2_COUNTERFACTUAL_CANARY_V4_METHOD_2026-10-05.md"
GATE = ROOT / "data/e1c_evaluation_2_counterfactual_dev_result.json"
runtime = frame.controller.runtime
_method, _bind, _live_preflight = frame.method, frame.bind_live, frame.live_preflight
FILES = (
    "evals/e1c_evaluation_2_counterfactual_canary_v4.py",
    "evals/e1c_evaluation_2_counterfactual_contract.py",
    "evals/e1c_evaluation_2_counterfactual_dev.py",
    "evals/e1c_evaluation_2_hybrid_dev_v3.py",
    "evals/e1c_evaluation_2_counterfactual_fast_dev.py",
    "docs/research/E1C2_COUNTERFACTUAL_CANARY_V4_METHOD_2026-10-05.md",
    "docs/research/E1C2_COUNTERFACTUAL_DEV_PROTOCOL_2026-10-05.md",
    "docs/research/E1C2_COUNTERFACTUAL_FAST_INPUT_2026-10-05.md",
)


def method():
    value = _method()
    gate = json.loads(GATE.read_bytes())
    if gate.get("reference_four_retained") is not True:
        raise ValueError("fresh DEV did not retain reference coverage")
    value.update({"schema": "e1c2-counterfactual-canary-v4-method-freeze", "dev_evidence_scope": "human-audited observable behavior, not exact original error site",
                  "method_files": {**value["method_files"], **{name: _sha(ROOT / name) for name in FILES}}})
    return value


def configure_frame():
    frame.OUT, frame.FREEZE, frame.IDENTITY, frame.PROTOCOL, frame.GATE = OUT, FREEZE, IDENTITY, PROTOCOL, GATE
    frame.SALT = "e1c2-counterfactual-independent-canary-v4-2026-10-05"
    frame.method, frame.live_preflight, frame.live_inputs = method, live_preflight, inputs


def bind_live():
    _bind()
    runtime.execute_role, runtime.model_messages, runtime.preflight = cf.execute_role, cf.messages, live_preflight


def public():
    rows = frame.stage.public()
    for row in rows:
        iid = row["instance_id"]
        seed = frame.stage.PUBLIC / iid / "frozen_input_v4.json"
        if not seed.is_file():
            continue
        frozen = cf.dev.path_input(json.loads(seed.read_bytes()), frame.stage.SOURCE / iid)
        frozen["seed_input_sha256"] = _sha(seed)
        path = frame.stage.PUBLIC / iid / "frozen_input_counterfactual_v1.json"
        if path.exists():
            if json.loads(path.read_bytes()) != frozen:
                raise ValueError("canary production input changed")
        else:
            _save(path, frozen)
    return rows


def inputs():
    rows = []
    for task in frame.stage.materialize.rows():
        iid = task["instance_id"]
        phases = [frame.stage.GRADER / iid / f"{phase}.json" for phase in ("base", "gold")]
        if not all(path.is_file() and json.loads(path.read_bytes()).get("phase_pass") is True for path in phases):
            continue
        path = frame.stage.PUBLIC / iid / "frozen_input_counterfactual_v1.json"
        frozen, workspace = json.loads(path.read_bytes()), frame.stage.SOURCE / iid
        if frozen["seed_input_sha256"] != _sha(frame.stage.PUBLIC / iid / "frozen_input_v4.json"):
            raise ValueError("frozen public seed changed")
        head = subprocess.check_output(["git", "-C", str(workspace), "rev-parse", "HEAD"], encoding="utf-8", timeout=30).strip()
        dirty = subprocess.check_output(["git", "-C", str(workspace), "status", "--porcelain", "--untracked-files=all"], encoding="utf-8", timeout=90).strip()
        if head != frozen["base_commit"] or dirty:
            raise ValueError("canary source must remain clean at frozen base")
        list(source_trees(frozen, workspace))
        rows.append((iid, frozen, path, workspace, frame.stage.materialize.verified_image(iid)))
    if not rows:
        raise ValueError("no dual-admitted tasks; provider must not start")
    return rows


def live_preflight():
    bind_live()
    value = _live_preflight()
    runtime.execute_role, runtime.preflight = cf.execute_role, live_preflight
    value.update({"schema": "e1c2-counterfactual-canary-v4-live-freeze", "counterfactual_runner_sha256": _sha(ROOT / FILES[0]),
                  "explicit_abstention_and_failed_derived_control_stop": True})
    return value


async def run():
    frozen_run = json.loads((runtime.OUT / "freeze.json").read_bytes())
    if frozen_run != runtime.preflight():
        raise ValueError("canary method/input changed")
    ledger, state_path = runtime.OUT / "provider_calls.jsonl", runtime.OUT / "state.json"
    if ledger.exists() or state_path.exists():
        raise FileExistsError("canary already started; no retry")
    if not runtime.settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek credential unavailable")
    state = {"status": "running", "fixed_denominator": 3, "rows": [], "trusted_reproducer_count": 0}
    _save(state_path, state)
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=120) as client:
            model = runtime.RawJsonFlash(model="deepseek-flash", temperature=0, streaming=False, max_retries=0,
                openai_api_base="https://api.deepseek.com", openai_api_key=runtime.settings.DEEPSEEK_API_KEY, http_async_client=client)
            for row, (iid, frozen, _, workspace, image) in zip(frozen_run["tasks"], runtime.inputs(), strict=True):
                final = {"instance_id": iid, "status": "no_repeatable_witness", "roles": [], "selected_role": None}
                for role in ("B", "A"):
                    response = await runtime.budgeted_ainvoke(model.bind(response_format={"type": "json_object"}) if role == "B" else model,
                        runtime.model_messages(frozen, role), {"configurable": {
                            "provider_ledger_path": str(ledger), "provider_run_id": OUT.name, "provider_task_id": iid,
                            "provider_total_token_ceiling": 60000, "provider_task_token_ceiling": 20000,
                            "provider_max_calls_per_task": 2, "provider_max_output_tokens": 3000,
                            "provider_prompt_reserve_multiplier": 1.4, "provider_disable_thinking": True}}, role=f"e1c2_hybrid_{role}")
                    record, root = runtime.response_record(response), runtime.OUT / iid / role
                    _save(root / "response.json", record)
                    try:
                        if record["response_status"] != "received":
                            result = {"status": "response_" + record["response_status"]}
                        else:
                            parsed = parse_response(record["raw"], role)
                            result = {"status": "abstained", "reason": parsed["reason"]} if parsed["status"] == "abstained" else runtime.execute_role(
                                role, parsed["payload"], frozen, workspace, image, root, row["environment"])
                    except (ValueError, SyntaxError, TypeError) as exc:
                        result = {"status": "candidate_rejected", "reason": f"{type(exc).__name__}: {exc}"}
                    final["roles"].append({"role": role, **result})
                    if runtime.failure_signal(result):
                        candidate = json.loads((root / "candidate.json").read_bytes())
                        _save(runtime.OUT / iid / "candidate.json", candidate)
                        _save(runtime.OUT / iid / "execution.json", json.loads((root / "execution.json").read_bytes()))
                        shutil.copytree(root / "execution", runtime.OUT / iid / "execution")
                        if _sha(runtime.OUT / iid / "execution" / (candidate["probe_sha256"] + ".py")) != candidate["probe_sha256"]:
                            raise ValueError("selected probe copy changed")
                        final.update({"status": "executed", "selected_role": role,
                                      "repeatable_failure_candidate": result["repeatable_failure_candidate"],
                                      "repeatable_nonsetup_failure": result["repeatable_nonsetup_failure"]})
                        break
                    if not cf.should_fallback(result):
                        final["status"] = result["status"]
                        break
                state["rows"].append(final)
                state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(json.dumps(final, ensure_ascii=False), flush=True)
    except Exception as exc:
        state.update({"status": "interrupted_no_auto_retry", "error": f"{type(exc).__name__}: {exc}"})
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise
    state["status"] = "completed"
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "completed", "attempted": len(state["rows"]), "fixed_denominator": 3}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze-method", "select", "metadata", "transport", "download", "admit", "public", "preflight", "run", "gold"))
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--timeout-per-image", type=int, default=21600)
    args = parser.parse_args()
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    configure_frame()
    if args.command in {"freeze-method", "select"}:
        result = frame.freeze_method() if args.command == "freeze-method" else frame.select_identity()
    else:
        frame.bind_stages()
        if args.command == "metadata":
            result = frame.stage.metadata.acquire()
        elif args.command == "transport":
            result = frame.audit_transport()
        elif args.command == "download":
            frame.audit_transport()
            result = frame.stage.acquire.acquire(timeout_per_image=args.timeout_per_image)
        elif args.command == "admit":
            result = frame.stage.admit(args.timeout)
        elif args.command == "public":
            result = public()
        else:
            bind_live()
            result = runtime.freeze() if args.command == "preflight" else asyncio.run(run()) if args.command == "run" else frame.grade()
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
