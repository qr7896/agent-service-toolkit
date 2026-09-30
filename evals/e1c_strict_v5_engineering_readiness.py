"""Aggregate Playbook A-E zero-provider engineering readiness."""

from __future__ import annotations

import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_stage_a_gate import build as stage_a
from evals.e1c_strict_v5_stage_b_gate import build as stage_b
from evals.e1c_strict_v5_stage_c_gate import build as stage_c
from evals.e1c_strict_v5_stage_d_gate import build as stage_d
from evals.e1c_strict_v5_stage_e_gate import build as stage_e

OUT = ROOT / "data" / "e1c_strict_v5_engineering_readiness.json"


def build(output: Path = OUT) -> dict:
    a = stage_a()
    b = stage_b()
    c = stage_c()
    d = stage_d()
    e = stage_e()
    checks = {
        "stage_a_ready": a.get("stage_a_ready") is True,
        "stage_b_ready": b.get("stage_b_ready") is True,
        "stage_c_ready": c.get("stage_c_ready") is True,
        "stage_d_engineering_ready": d.get("stage_d_engineering_ready") is True,
        "stage_e_engineering_ready": e.get("stage_e_engineering_ready") is True,
    }
    ready = all(checks.values())
    result = {
        "schema": "e1c-strict-v5-engineering-readiness-v1",
        "engineering_ready_a_through_e": ready,
        "checks": checks,
        "independent_canary_admission_ready": False,
        "trusted_reproducer_requirement_met": False,
        "provider_calls": 0,
        "live_model_run": False,
        "live_allowed": False,
        "c5_allowed": False,
        "fresh30_allowed": False,
        "reason": (
            "a_through_e_zero_provider_engineering_ready_but_canary_admission_closed"
            if ready
            else "a_through_e_engineering_incomplete"
        ),
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
