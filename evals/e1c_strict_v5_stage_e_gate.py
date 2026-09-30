"""Playbook Stage-E localization/inspect safety engineering gate."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_blind_boundary import BlindBoundaryViolation
from evals.e1c_strict_v5_runtime import build_bundle, inspect_candidate

OUT = ROOT / "data" / "e1c_strict_v5_stage_e_gate.json"


def build(output: Path = OUT) -> dict:
    checks: dict[str, bool] = {}
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        pkg = workspace / "pkg"
        pkg.mkdir()
        (pkg / "engine.py").write_text(
            "def normalize_value(value):\n    return value\n\n"
            "def process_value(value):\n    return normalize_value(value)\n",
            encoding="utf-8",
        )
        tests = workspace / "tests"
        tests.mkdir()
        (tests / "test_engine.py").write_text(
            "def test_hidden():\n    assert normalize_value(3) == 4\n",
            encoding="utf-8",
        )
        bundle = build_bundle(
            statement="normalize_value should preserve supported values.",
            workspace=workspace,
            base_commit="b" * 40,
        )
        checks["candidate_count_bounded"] = (
            0 < bundle["localization"]["candidate_count"]
            <= bundle["localization"]["max_candidate_count"]
            <= 6
        )
        checks["candidate_paths_production_only"] = all(
            not path.startswith("tests/") for path in bundle["candidate_paths"]
        )
        path = bundle["candidate_paths"][0]
        first = inspect_candidate(bundle, workspace, path)
        checks["inspect_read_cost_bounded"] = first["read_cost"] <= int(
            bundle["inspect_budget"]["max_chars"]
        )
        try:
            inspect_candidate(bundle, workspace, path, prior_inspections=(first,))
        except BlindBoundaryViolation:
            checks["second_inspect_rejected"] = True
        else:
            checks["second_inspect_rejected"] = False
        try:
            inspect_candidate(bundle, workspace, "tests/test_engine.py")
        except BlindBoundaryViolation:
            checks["unfrozen_test_path_rejected"] = True
        else:
            checks["unfrozen_test_path_rejected"] = False

    ready = all(checks.values())
    result = {
        "schema": "e1c-strict-v5-stage-e-gate-v1",
        "stage_e_engineering_ready": ready,
        "reason": (
            "stage_e_localization_and_safety_ready"
            if ready
            else "stage_e_localization_or_safety_incomplete"
        ),
        "checks": checks,
        "official_repair_claim_allowed": False,
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
