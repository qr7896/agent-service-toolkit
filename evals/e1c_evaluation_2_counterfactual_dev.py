"""Old-DEV counterfactual control audit/replay and separately frozen Flash study."""

from __future__ import annotations

import argparse
import asyncio
import json

from evals import e1c_evaluation_2_hybrid_dev_v3 as dev
from evals import e1c_evaluation_2_hybrid_oracle_replay as cache
from evals.e1c_evaluation_2_contract_method import parse_response
from evals.e1c_evaluation_2_counterfactual_contract import compile_pair
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_source_contract import build_source_pair

runtime = dev.runtime
OUT = ROOT / ".codex/e1c/evaluation_2/counterfactual-dev-v1"
AUDIT = ROOT / ".codex/e1c/evaluation_2/counterfactual-audit-dev-v1"
REPLAY = ROOT / ".codex/e1c/evaluation_2/counterfactual-replay-dev-v1"
SOURCE = ROOT / ".codex/e1c/evaluation_2/hybrid-dev-v3"
PROTOCOL = ROOT / "docs/research/E1C2_COUNTERFACTUAL_DEV_PROTOCOL_2026-10-05.md"
_dev_preflight, _fallback = dev.preflight, dev.should_fallback
_execute, _messages = dev.controller.execute_role, runtime.model_messages
MODULES = ("evals/e1c_evaluation_2_counterfactual_dev.py", "evals/e1c_evaluation_2_counterfactual_contract.py")


def binding():
    return {"counterfactual_modules": {name: _sha(ROOT / name) for name in MODULES}, "counterfactual_protocol_sha256": _sha(PROTOCOL)}


def execute_role(role, payload, frozen, workspace, image, root, environment):
    proof = {"compiled": False}
    if role == "B":
        payload, proof = compile_pair(payload, frozen, workspace)
        _save(root / "counterfactual_control.json", proof)
    result = _execute(role, payload, frozen, workspace, image, root, environment)
    if proof["compiled"] and result.get("control_pass") is False:
        return {"status": "fixture_contract_rejected", "control_pass": False,
                "reason": "same-literal control did not pass production preconditions; no target or fallback"}
    return result


def messages(frozen, role):
    result = _messages(frozen, role)
    if role == "B":
        result[0].content += (
            " A representation-only contrast must preserve identical literal elements, order and length. "
            "Do not reduce a collection's size or change values to make the control pass. "
            "Construct all fixture dimensions and named metadata consistently with production guards. "
            "Changing a representation is not permission to introduce a second invalid precondition. "
            "If this cannot be grounded in the provided production source, abstain."
        )
    return result


def should_fallback(result):
    return result.get("status") != "fixture_contract_rejected" and _fallback(result)


def configure():
    dev.OUT, dev.PROTOCOL = OUT, PROTOCOL
    dev.preflight, dev.should_fallback = preflight, should_fallback
    dev.configure()
    runtime.execute_role, runtime.model_messages, runtime.preflight = execute_role, messages, preflight


def preflight():
    configure()
    value = _dev_preflight()
    runtime.execute_role, runtime.preflight = execute_role, preflight
    value.update({"schema": "e1c2-counterfactual-dev-v1-freeze", **binding()})
    return value


def audit():
    freeze = json.loads((SOURCE / "freeze.json").read_bytes())
    state = json.loads((SOURCE / "state.json").read_bytes())
    if state["status"] != "completed" or len(state["rows"]) != 9:
        raise ValueError("completed fixed old DEV required")
    _save(AUDIT / "freeze.json", {**binding(), "source_freeze_sha256": _sha(SOURCE / "freeze.json"),
                                "source_state_sha256": _sha(SOURCE / "state.json"), "provider_calls": 0})
    rows = []
    for task in freeze["tasks"]:
        iid = task["instance_id"]
        path = SOURCE / "inputs" / f"{iid}.json"
        if _sha(path) != task["input_sha256"] or runtime.verified_local_image(iid) != task["image_id"]:
            raise ValueError("cached DEV input/image changed")
        frozen = json.loads(path.read_bytes())
        response = SOURCE / iid / "B/response.json"
        parsed = parse_response(json.loads(response.read_bytes())["raw"], "B")
        row = {"instance_id": iid, "response_sha256": _sha(response), "provider_calls": 0}
        if parsed["status"] == "abstained":
            row["status"] = "abstained"
        else:
            workspace = runtime.coverage.SOURCE / iid
            changed, proof = compile_pair(parsed["payload"], frozen, workspace)
            row.update(proof)
            if proof["compiled"]:
                control, _, _ = build_source_pair(changed, frozen, workspace)
                executions = [runtime.execute_candidate(control, task["image_id"], frozen["base_commit"], AUDIT / iid / f"control-{n}",
                              missing_optional_import=task["environment"]["missing_optional_import"]) for n in (1, 2)]
                row["derived_control_runs"] = executions
                row["derived_control_pass"] = all(e["runs"] and all(r["returncode"] == 0 and not r["timed_out"] for r in e["runs"]) for e in executions)
        rows.append(row)
        print(json.dumps({key: row[key] for key in ("instance_id", "status", "derived_control_pass") if key in row}), flush=True)
    result = {"rows": rows, "fixed_denominator": 12, "provider_calls": 0, "independent_validation": False}
    _save(AUDIT / "result.json", result)
    return result


def replay_preflight():
    return {**cache.preflight(), **binding(), "schema": "e1c2-counterfactual-cache-replay-v1", "provider_calls": 0}


def replay():
    cache.OUT = REPLAY
    cache.configure()
    runtime.execute_role, runtime.preflight = execute_role, replay_preflight
    runtime.freeze()
    asyncio.run(runtime.run())
    return {"provider_calls": 0, "result": runtime.grade(), "independent_validation": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "replay", "preflight", "run", "gold"))
    args = parser.parse_args()
    if args.command in {"audit", "replay"}:
        result = audit() if args.command == "audit" else replay()
    else:
        configure()
        result = runtime.freeze() if args.command == "preflight" else asyncio.run(dev.run()) if args.command == "run" else runtime.grade()
    print(json.dumps(result, ensure_ascii=False))
