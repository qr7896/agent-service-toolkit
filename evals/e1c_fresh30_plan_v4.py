"""Zero-provider Fresh30-v4 plan. It never selects or materializes new tasks."""

from __future__ import annotations

import argparse
import json

from evals.e1c_fresh30_gate_v4 import gate


def plan() -> dict:
    current_gate = gate()
    phases = [
        {"phase": "A_independent_canary", "entry": "external metadata-only canary identity frozen before statement materialization", "exit": ">=1 treatment-only official resolved; 0 baseline-only; no anomaly"},
        {"phase": "B_C5_same_version_n30", "entry": "independent canary exit satisfied", "exit": "30 attempted / 30 official resolved / completed"},
        {"phase": "C_fresh30_identity_freeze", "entry": "same-version C5 30/30", "exit": "fresh 30-task metadata manifest frozen before task-content read"},
        {"phase": "D_fresh30_materialize_and_admit", "entry": "fresh identity frozen", "exit": "30/30 source identity + official image + Base-Fail + independent Gold-Pass"},
        {"phase": "E_fresh30_one_shot", "entry": "admission 30/30 and config freeze", "exit": "one-shot result + audit + statistics package"},
    ]
    return {
        "schema": "e1c-fresh30-v4-plan-v1",
        "provider_calls": 0,
        "gate_ready": current_gate["ready"],
        "gate_reason": current_gate["reason"],
        "new_task_tree_touched": False,
        "materialization_allowed_now": current_gate["ready"],
        "target_task_count": 30,
        "selection_constraints": [
            "disjoint from all prior E1-C development/canary/formal task identities",
            "metadata identity frozen before statement/test/gold content is read",
            "no outcome-conditioned replacement after freeze",
            "official image digest and exact base source identity required",
            "Base-Fail and independent Gold-Pass required for every admitted task",
        ],
        "measurement": {
            "primary": "official resolved / 30",
            "paired_canary_primary": "treatment-only official resolved",
            "secondary": ["model calls", "provider tokens", "files read", "tool calls", "abstentions", "blind reproducer coverage", "verification failures", "infrastructure failures"],
            "denominator_policy": "all frozen and admitted tasks retained",
        },
        "phases": phases,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("plan",))
    parser.parse_args()
    print(json.dumps(plan(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
