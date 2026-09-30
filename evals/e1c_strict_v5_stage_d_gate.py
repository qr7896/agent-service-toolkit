"""Playbook Stage-D task-agnostic reproducer engineering gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_strict_v5_probe import (
    _adjudicate_runs,
    candidate_probes,
    freeze_probe_plan,
    render_probe,
)

OUT = ROOT / "data" / "e1c_strict_v5_stage_d_gate.json"


def build(output: Path = OUT) -> dict:
    source = "def normalize_value(value):\n    return value\n"
    digest = hashlib.sha256(source.encode()).hexdigest()
    localization = {
        "candidates": [
            {
                "path": "pkg/engine.py",
                "symbol": "normalize_value",
                "start_line": 1,
                "end_line": 2,
                "origin": "issue_ast_definition",
                "depth": 0,
                "source_sha256": digest,
                "read_cost": len(source),
                "rank": 1,
                "text": source,
            }
        ],
        "candidate_paths": ["pkg/engine.py"],
    }
    issue = "normalize_value(3) should return 4."
    probes = candidate_probes(issue, localization)
    probe = probes[0] if probes else None
    runs = [
        {
            "exit_code": 8,
            "stdout": "STRICT_V5_CONTRACT_MISMATCH:return_equals\n",
            "stderr": "",
            "timed_out": False,
        },
        {
            "exit_code": 8,
            "stdout": "STRICT_V5_CONTRACT_MISMATCH:return_equals\n",
            "stderr": "",
            "timed_out": False,
        },
    ]
    adjudicated = _adjudicate_runs(probe, runs, network_isolated=True) if probe else {}
    no_contract = freeze_probe_plan(
        "Normalization behaves incorrectly in an edge case.",
        localization,
    )
    checks = {
        "probe_generated_from_prose": len(probes) == 1,
        "benchmark_assertion_not_used": bool(probe)
        and probe.get("benchmark_assertion_used") is False,
        "task_id_not_used": bool(probe) and probe.get("task_id_used") is False,
        "rendered_probe_has_no_assert_statement": bool(probe)
        and "assert " not in render_probe(probe),
        "stable_isolated_failure_trusted": adjudicated.get("trusted_reproducer") is True,
        "stable_failure_status": adjudicated.get("status") == "reproduced_failure",
        "unsafe_or_unexpressed_contract_abstains": no_contract.get("status")
        == "no_reproducer"
        and no_contract.get("trusted_reproducer") is False,
    }
    ready = all(checks.values())
    result = {
        "schema": "e1c-strict-v5-stage-d-gate-v1",
        "stage_d_engineering_ready": ready,
        "reason": (
            "stage_d_reproducer_engineering_ready"
            if ready
            else "stage_d_reproducer_engineering_incomplete"
        ),
        "checks": checks,
        "independent_canary_trusted_reproducer_requirement_met": False,
        "minimum_canary_trusted_reproducers": 2,
        "provider_calls": 0,
        "live_model_run": False,
        "live_allowed": False,
        "c5_allowed": False,
        "fresh30_allowed": False,
        "engineering_gate_only": True,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
