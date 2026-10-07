"""Zero-provider first-probe audit of sealed V4 OLD DEV; no best-of or live run."""

from __future__ import annotations

import argparse
import json
import shutil

from evals import e1c_evaluation_2_bounded_repro_loop as loop
from evals.e1c_evaluation_2_bounded_repro_dev import inputs as old_inputs
from evals.e1c_evaluation_2_bounded_repro_dev_v3 import parse_action
from evals.e1c_evaluation_2_container_health import require_engine
from evals.e1c_evaluation_2_contract_recovery import compile_contract, failure_phase
from evals.e1c_evaluation_2_counterfactual_fast_dev import verify_workspace
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

PREVIOUS = ROOT / ".codex/e1c/evaluation_2/bounded-runtime-dev-v4"
OUT = ROOT / ".codex/e1c/evaluation_2/contract-recovery-zero-dev-v1"
PROTOCOL = ROOT / "docs/research/E1C2_CONTRACT_RECOVERY_ZERO_DEV_V1_2026-10-07.md"
PINNED = {"freeze.json": "ab09fc427cb29b9d867aa1801dcea9763f5c9ad10fd70ce09231fed2527d480a",
          "state.json": "a6d7b84ef22a5ff692aac24ae5bd9cfb5ca4d49badadd779937dc072ab78c7dc",
          "provider_calls.jsonl": "8b6cc8c3b1e98f0e96066d7f867815a506bd2afd030e865d905a92d055e876de",
          "generation-seal.json": "f4873fa7b12ee2090e6581cdfe04c3345e6604a7463e6233c9a64363b09a2522"}


def records():
    if any(_sha(PREVIOUS / n) != h for n, h in PINNED.items()):
        raise ValueError("sealed V4 records changed")
    seal = json.loads((PREVIOUS / "generation-seal.json").read_bytes())
    if any(_sha(PREVIOUS / n) != h for n, h in seal["files"].items()):
        raise ValueError("sealed cache file changed")
    rows = []
    for task, _, workspace in old_inputs():
        iid = task["instance_id"]
        for path in sorted((PREVIOUS / iid).glob("turn-*/response.json")):
            response = json.loads(path.read_bytes())
            action, payload = parse_action(response["raw"])
            if action != "probe":
                continue
            frozen = json.loads((path.parent / "input.json").read_bytes())
            verify_workspace(frozen, workspace)
            rows.append((task, frozen, workspace, path, payload))
            break
    if len(rows) != 3:
        raise ValueError("expected one first probe per each OLD DEV repository")
    return rows


def preflight():
    rows = records()
    require_engine(tuple(t["image_id"] for t, *_ in rows))
    modules = json.loads((PREVIOUS / "freeze.json").read_bytes())["method_sha256"]
    for name in modules:
        if _sha(ROOT / name) != modules[name]:
            raise ValueError("original frozen method changed")
    return {"schema": "e1c2-contract-recovery-zero-freeze-v1", "fixed_denominator": 12, "screen_denominator": 3,
            "provider_calls": 0, "provider_tokens": 0, "cached_not_fresh_model_result": True,
            "first_probe_rule_not_best_of": True, "previous_records": PINNED,
            "tasks": [{**t, "cached_response_sha256": _sha(p), "cached_input_sha256": _sha(p.parent / "input.json")}
                      for t, _, _, p, _ in rows],
            "method_sha256": {**modules, **{n: _sha(ROOT / n) for n in (
                "evals/e1c_evaluation_2_contract_recovery.py", "evals/e1c_evaluation_2_contract_recovery_zero.py")}},
            "protocol_sha256": _sha(PROTOCOL)}


def zero():
    if OUT.exists():
        raise FileExistsError("zero recovery already started; preserve it, no automatic retry")
    frozen_run = preflight()
    _save(OUT / "freeze.json", frozen_run)
    state = {"status": "running", "fixed_denominator": 12, "screen_denominator": 3,
             "provider_calls": 0, "trusted_reproducer_count": 0, "rows": []}
    _save(OUT / "state.json", state)
    for task, frozen, workspace, response_path, payload in records():
        iid, root = task["instance_id"], OUT / task["instance_id"]
        row = {"instance_id": iid, "cached_response_sha256": _sha(response_path)}
        old_control, old_execution = response_path.parent / "control_candidate.json", response_path.parent / "control-1.json"
        if old_control.exists() and old_execution.exists():
            _save(root / "old_control_phase.json", failure_phase(json.loads(old_control.read_bytes()), json.loads(old_execution.read_bytes()), payload))
        try:
            canonical, proof = compile_contract(payload, frozen, workspace)
            _save(root / "normalization_proof.json", proof)
            result, _, candidate, execution = loop.execute_probe(canonical, frozen, workspace, task["image_id"], root / "compiled", task["environment"])
            if candidate:
                _save(root / "candidate.json", candidate)
                _save(root / "execution.json", execution)
                shutil.copytree(root / "compiled/execution", root / "execution")
                result["status"] = "executed"
            row.update(result)
        except (ValueError, SyntaxError, TypeError) as exc:
            row.update({"status": "unsupported_or_invalid_contract", "reason": str(exc)[:250]})
        state["rows"].append(row)
        (OUT / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: row[k] for k in ("instance_id", "status", "reason") if k in row}), flush=True)
    state["status"] = "completed"
    (OUT / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _save(OUT / "generation-seal.json", {"files": {p.relative_to(OUT).as_posix(): _sha(p) for p in sorted(OUT.rglob("*")) if p.is_file()},
                                         "selection_before_grader": True})
    return state


def grade():
    seal = json.loads((OUT / "generation-seal.json").read_bytes())
    if any(_sha(OUT / n) != h for n, h in seal["files"].items()):
        raise ValueError("zero replay changed before independent score")
    from evals import e1c_evaluation_2_unified_dev_v2_gold as grader

    grader.base.OUT, grader.base.FREEZE, grader.base.preflight = OUT, OUT / "freeze.json", preflight
    grader.OUT = OUT / "gold-discrimination"
    return grader.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("zero", "gold"))
    args = parser.parse_args()
    print(json.dumps(zero() if args.command == "zero" else grade(), ensure_ascii=False))
