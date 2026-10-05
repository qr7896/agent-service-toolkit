"""Zero-provider, all-task DEV replay of cached v2 outputs under source contracts."""

from __future__ import annotations

import argparse
import importlib
import json

from evals import e1c_evaluation_2_contract_ab_dev_v2 as previous
from evals.e1c_evaluation_2_contract_method import parse_response
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_probe import execute_candidate, validate_candidate
from evals.e1c_evaluation_2_source_contract import build_source_pair, optional_import

OUT = ROOT / ".codex/e1c/evaluation_2/source-contract-replay-dev-v1"
PROTOCOL = ROOT / "docs/research/E1C2_SOURCE_CONTRACT_REPLAY_DEV_PROTOCOL_2026-10-05.md"


def preflight(arm):
    actual = previous.preflight(arm)
    root = previous.OUT / arm
    if actual != json.loads((root / "freeze.json").read_bytes()) or json.loads((root / "state.json").read_bytes())["status"] != "completed":
        raise ValueError("cached v2 arm is not complete and unchanged")
    tasks = []
    for row, (iid, frozen, _) in zip(actual["tasks"], previous.prepare(), strict=True):
        environment = optional_import(frozen, previous.original.SOURCE / iid)
        tasks.append({**row, "missing_optional_import": environment["missing_optional_import"],
                      "environment_source_evidence": environment["evidence"],
                      "cached_response_sha256": _sha(root / iid / "response.json")})
    return {"schema": "e1c2-source-contract-cached-replay-freeze-v1", "arm": arm, "tasks": tasks,
            "fixed_denominator": 12, "selection": "all_nine_cached_v2_tasks_no_outcome_selection", "provider_calls": 0,
            "upstream_freeze_sha256": _sha(root / "freeze.json"), "upstream_state_sha256": _sha(root / "state.json"),
            "protocol_sha256": _sha(PROTOCOL), "modules": {name: _sha(ROOT / name) for name in (
                "evals/e1c_evaluation_2_source_contract_replay.py", "evals/e1c_evaluation_2_source_contract.py")}}


def freeze(arm):
    value = preflight(arm)
    path = OUT / arm / "freeze.json"
    if path.exists():
        if json.loads(path.read_bytes()) != value:
            raise ValueError("source-contract replay freeze changed")
    else:
        _save(path, value)
    return value


def run(arm):
    frozen_run = json.loads((OUT / arm / "freeze.json").read_bytes())
    if frozen_run != preflight(arm):
        raise ValueError("source-contract replay inputs changed")
    state_path = OUT / arm / "state.json"
    if state_path.exists():
        raise FileExistsError("replay already started; no silent rerun")
    state = {"status": "running", "provider_calls": 0, "rows": [], "trusted_reproducer_count": 0}
    _save(state_path, state)
    for row, (iid, frozen, _) in zip(frozen_run["tasks"], previous.prepare(), strict=True):
        directory = OUT / arm / iid
        response = json.loads((previous.OUT / arm / iid / "response.json").read_bytes())
        result = {"instance_id": iid, "status": "cached_response", "cached_response_sha256": row["cached_response_sha256"]}
        try:
            parsed = parse_response(response["raw"], arm)
            if parsed["status"] == "abstained":
                result.update({"status": "abstained", "reason": parsed["reason"]})
            else:
                if arm == "B":
                    control, target, frontier = build_source_pair(parsed["payload"], frozen, previous.original.SOURCE / iid)
                    _save(directory / "frontier.json", frontier)
                    _save(directory / "control_candidate.json", control)
                    controls = [execute_candidate(control, row["image_id"], frozen["base_commit"], directory / f"control-{n}",
                                missing_optional_import=row["missing_optional_import"]) for n in (1, 2)]
                    _save(directory / "control_execution.json", {"runs": controls})
                    passes = all(all(r["returncode"] == 0 and not r["timed_out"] for r in item["runs"]) for item in controls)
                    result["control_pass"] = passes
                else:
                    target = validate_candidate(parsed["payload"]["source"], frozen["issue"].splitlines()[0],
                                                frozen, workspace=previous.original.SOURCE / iid)
                    passes = True
                _save(directory / "candidate.json", target)
                if not passes:
                    result["status"] = "fixture_or_positive_control_failed"
                else:
                    execution = execute_candidate(target, row["image_id"], frozen["base_commit"], directory / "execution",
                                missing_optional_import=row["missing_optional_import"], repeat_nonsetup_failure=True)
                    _save(directory / "execution.json", execution)
                    result.update({"status": "executed", "repeatable_failure_candidate": execution["repeatable_failure_candidate"],
                                   "repeatable_nonsetup_failure": execution["repeatable_nonsetup_failure"]})
        except (ValueError, SyntaxError, TypeError) as exc:
            result.update({"status": "candidate_rejected", "reason": f"{type(exc).__name__}: {exc}"})
        state["rows"].append(result)
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False), flush=True)
    state["status"] = "completed"
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return {"arm": arm, "attempted": len(state["rows"]), "provider_calls": 0}


def grade(arm):
    from evals import e1c_evaluation_2_unified_dev_v2_gold as gold

    if arm == "A":
        importlib.import_module("evals.e1c_evaluation_2_unified_dev_v4")
    gold.base.OUT, gold.base.FREEZE = OUT / arm, OUT / arm / "freeze.json"
    gold.base.preflight = lambda: preflight(arm)
    gold.GRADER, gold.OUT = previous.original.ADMISSION, OUT / arm / "gold-discrimination"
    return gold.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "gold"))
    parser.add_argument("--arm", choices=("A", "B"), default="B")
    args = parser.parse_args()
    value = freeze(args.arm) if args.command == "preflight" else run(args.arm) if args.command == "run" else grade(args.arm)
    print(json.dumps(value, ensure_ascii=False))
