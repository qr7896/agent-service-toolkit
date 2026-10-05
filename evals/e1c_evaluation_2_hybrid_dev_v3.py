"""Old DEV only: honor abstention and exact issue-provided production path anchors."""

from __future__ import annotations

import argparse
import ast
import asyncio
import json
import re
import shutil

import httpx

from evals import e1c_evaluation_2_hybrid_controller_v2 as controller
from evals.e1c_blind_boundary import BlindBoundaryViolation
from evals.e1c_evaluation_2_contract_method import parse_response
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

runtime = controller.runtime
OUT = ROOT / ".codex/e1c/evaluation_2/hybrid-dev-v3"
PROTOCOL = ROOT / "docs/research/E1C2_HYBRID_DEV_V3_PROTOCOL_2026-10-05.md"


def path_input(seed, workspace):
    """Exact existing paths, not glob/file-name guessing; no grader or task-ID input."""
    frozen = runtime.coverage.freeze_input(seed, workspace)
    issue, anchors = seed["issue"].replace("\\", "/"), []
    pattern = r"(?<![\w./])([A-Za-z_][\w.-]*(?:/[A-Za-z_][\w.-]*)+\.py)(?::(\d+))?"
    for match in re.finditer(pattern, issue):
        relative = match[1]
        try:
            if not runtime.coverage.production_path(relative):
                continue
            path = workspace / relative
            if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(workspace.resolve()):
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            ast.parse("\n".join(lines))
            before = re.findall(r"\bline\s+`?(\d+)`?", issue[max(0, match.start() - 80):match.start()], re.I)
            after = re.search(r"\bline\s+`?(\d+)`?", issue[match.end():match.end() + 60], re.I)
            center = int(match[2] or (before[-1] if before else after[1] if after else 1))
            if not 1 <= center <= len(lines):
                continue
            start = max(1, center - 12)
            text = "\n".join(lines[start - 1:start + 44])[:2500]
            anchors.append({"path": relative, "symbol": None, "owner": None, "start_line": start,
                            "end_line": start + text.count("\n"), "text": text,
                            "source_sha256": _sha(path), "origin": "exact_issue_production_path"})
        except (BlindBoundaryViolation, ValueError, SyntaxError, OSError):
            continue
    windows, seen = [], set()
    for row in [*anchors, *frozen["windows"]]:
        key = (row["path"], row["start_line"], row.get("symbol"), row.get("owner"))
        if key in seen or len(runtime.coverage.input_json({"issue": seed["issue"], "windows": [*windows, row]})) > 23000:
            continue
        audit_repair_visible_payload(row)
        windows.append(row)
        seen.add(key)
        if len(windows) == 4:
            break
    value = {**frozen, "schema": "e1c2-issue-path-production-input-v3", "windows": windows,
             "candidate_paths": [r["path"] for r in windows], "candidate_count": len(windows)}
    value.pop("input_sha256")
    value["input_sha256"] = audit_repair_visible_payload(value)
    return value


def inputs():
    rows = []
    for row in runtime.coverage.prepare()["rows"]:
        iid = row["instance_id"]
        workspace = runtime.coverage.SOURCE / iid
        seed = json.loads((runtime.coverage.ISSUE / iid / "frozen_input_v4.json").read_bytes())
        frozen = path_input(seed, workspace)
        path = OUT / "inputs" / f"{iid}.json"
        if path.exists():
            if json.loads(path.read_bytes()) != frozen:
                raise ValueError("DEV v3 production input changed")
        else:
            _save(path, frozen)
        rows.append((iid, frozen, path, workspace, runtime.verified_local_image(iid)))
    return rows


def configure():
    controller.OUT, controller.PROTOCOL = OUT, PROTOCOL
    controller.configure()
    runtime.inputs, runtime.preflight = inputs, preflight
    runtime.FIXED_DENOMINATOR, runtime.BATCH_CAP, runtime.TASK_CAP = 12, 80000, 20000


def preflight():
    configure()
    value = controller.preflight()
    runtime.preflight = preflight
    value.update({"schema": "e1c2-hybrid-old-dev-v3-freeze", "dev_v3_module_sha256": _sha(ROOT / "evals/e1c_evaluation_2_hybrid_dev_v3.py"),
                  "abstention_policy": "primary_explicit_abstention_stops_task_no_fallback",
                  "independent_validation": False})
    return value


def should_fallback(result):
    return result.get("status") != "abstained" and not runtime.failure_signal(result)


async def run():
    frozen_run = json.loads((OUT / "freeze.json").read_bytes())
    if frozen_run != preflight():
        raise ValueError("DEV v3 method changed")
    ledger, state_path = OUT / "provider_calls.jsonl", OUT / "state.json"
    if ledger.exists() or state_path.exists():
        raise FileExistsError("DEV v3 already started; no automatic retry")
    if not runtime.settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek credential unavailable")
    state = {"status": "running", "fixed_denominator": 12, "rows": [], "trusted_reproducer_count": 0}
    _save(state_path, state)
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=120) as client:
            model = runtime.RawJsonFlash(model="deepseek-flash", temperature=0, streaming=False, max_retries=0,
                openai_api_base="https://api.deepseek.com", openai_api_key=runtime.settings.DEEPSEEK_API_KEY, http_async_client=client)
            for row, (iid, frozen, _, workspace, image) in zip(frozen_run["tasks"], inputs(), strict=True):
                final = {"instance_id": iid, "status": "no_repeatable_witness", "roles": [], "selected_role": None}
                for role in ("B", "A"):
                    bound = model.bind(response_format={"type": "json_object"}) if role == "B" else model
                    response = await runtime.budgeted_ainvoke(bound, runtime.model_messages(frozen, role), {"configurable": {
                        "provider_ledger_path": str(ledger), "provider_run_id": OUT.name, "provider_task_id": iid,
                        "provider_total_token_ceiling": 80000, "provider_task_token_ceiling": 20000,
                        "provider_max_calls_per_task": 2, "provider_max_output_tokens": 3000,
                        "provider_prompt_reserve_multiplier": 1.4, "provider_disable_thinking": True}}, role=f"e1c2_hybrid_{role}")
                    record, root = runtime.response_record(response), OUT / iid / role
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
                        _save(OUT / iid / "candidate.json", candidate)
                        _save(OUT / iid / "execution.json", json.loads((root / "execution.json").read_bytes()))
                        shutil.copytree(root / "execution", OUT / iid / "execution")
                        if _sha(OUT / iid / "execution" / (candidate["probe_sha256"] + ".py")) != candidate["probe_sha256"]:
                            raise ValueError("selected probe copy changed")
                        final.update({"status": "executed", "selected_role": role,
                                      "repeatable_failure_candidate": result["repeatable_failure_candidate"],
                                      "repeatable_nonsetup_failure": result["repeatable_nonsetup_failure"]})
                        break
                    if not should_fallback(result):
                        final["status"] = "abstained"
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
    return {"attempted": len(state["rows"]), "status": "completed", "fixed_denominator": 12}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "gold"))
    args = parser.parse_args()
    configure()
    result = runtime.freeze() if args.command == "preflight" else asyncio.run(run()) if args.command == "run" else runtime.grade()
    print(json.dumps(result, ensure_ascii=False))
