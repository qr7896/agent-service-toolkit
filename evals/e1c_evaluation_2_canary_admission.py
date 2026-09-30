"""Run the existing official Base/Gold admission on the fixed canary identity."""

from __future__ import annotations

import argparse
import json

from evals import e1c_evaluation_2_admission as admission
from evals.e1c_evaluation_2_canary_materialize import GRADER, rows, verified_image
from evals.e1c_evaluation_2_canary_metadata import OUT as METADATA
from evals.e1c_evaluation_2_canary_select import IDENTITY


def run_phase(instance_id: str, phase: str, *, timeout: int = 900) -> dict:
    if instance_id not in {task["instance_id"] for task in rows()}:
        raise ValueError("task is outside the fixed canary")
    original = {name: getattr(admission, name) for name in ("IDENTITY", "METADATA", "OUT", "TREE", "verified_local_image")}
    try:
        admission.IDENTITY = IDENTITY
        admission.METADATA = METADATA
        admission.OUT = GRADER
        admission.TREE = GRADER / "frozen-task-blobs.json"
        admission.verified_local_image = verified_image
        return admission.run_phase(instance_id, phase, timeout=timeout)
    finally:
        for name, value in original.items():
            setattr(admission, name, value)


def run_all(*, timeout: int = 900) -> dict:
    outcomes = []
    tasks = rows()
    for task in tasks:
        iid = task["instance_id"]
        for phase in ("base", "gold"):
            print(f"canary admission {len(outcomes) + 1}/6: {iid} {phase}", flush=True)
            result = run_phase(iid, phase, timeout=timeout)
            summary = {key: result[key] for key in ("instance_id", "phase", "phase_pass", "returncode", "f2p_total", "f2p_explicit_fail", "f2p_pass")}
            outcomes.append(summary)
            print(json.dumps(summary, ensure_ascii=False), flush=True)
    return {"phase_count": len(outcomes), "dual_admitted": sum(all(row["phase_pass"] for row in outcomes[n:n + 2]) for n in (0, 2, 4)), "provider_calls": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run",))
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    print(json.dumps(run_all(timeout=args.timeout), ensure_ascii=False))
