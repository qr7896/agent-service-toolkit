"""Old-DEV-only simulation: choose a base witness before reading its Gold verdict."""

from __future__ import annotations

import json
from pathlib import Path

from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

OUT = ROOT / ".codex/e1c/evaluation_2/source-contract-replay-dev-v1"


def failure_signal(row):
    return row.get("status") == "executed" and bool(row.get("repeatable_failure_candidate") or row.get("repeatable_nonsetup_failure"))


def choose(primary, fallback):
    if primary.get("control_pass") is True and failure_signal(primary):
        return "B"
    return "A" if failure_signal(fallback) else None


def simulate():
    states = {arm: json.loads((OUT / arm / "state.json").read_bytes()) for arm in ("A", "B")}
    if any(state["status"] != "completed" for state in states.values()):
        raise ValueError("complete cached replays required")
    rows = {arm: {row["instance_id"]: row for row in state["rows"]} for arm, state in states.items()}
    if set(rows["A"]) != set(rows["B"]) or len(rows["A"]) != 9:
        raise ValueError("paired replay identities differ")
    selected = [{"instance_id": iid, "selected_arm": choose(rows["B"][iid], rows["A"][iid])} for iid in rows["A"]]
    value = {"schema": "e1c2-pregrader-policy-DEV-simulation-v1", "development_after_DEV_outcomes": True,
             "independent_validation": False, "fixed_denominator": 12, "provider_calls": 0,
             "policy_sha256": _sha(Path(__file__)), "replay_state_sha256": {a: _sha(OUT / a / "state.json") for a in ("A", "B")},
             "rows": selected}
    lock = OUT / "pregrader-selection.json"
    if lock.exists():
        if json.loads(lock.read_bytes()) != value:
            raise ValueError("existing pregrader selection differs")
    else:
        _save(lock, value)
    graded = []
    for row in selected:
        arm = row["selected_arm"]
        if arm:
            result = json.loads((OUT / arm / "gold-discrimination" / row["instance_id"] / "result.json").read_bytes())
            graded.append({**row, "gold_discriminating": result["gold_discriminating"]})
    return {"selected": len(graded), "gold_discriminating": sum(row["gold_discriminating"] for row in graded),
            "fixed_denominator": 12, "provider_calls": 0, "independent_validation": False, "rows": graded}


if __name__ == "__main__":
    print(json.dumps(simulate()))
