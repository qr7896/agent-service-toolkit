"""Playbook Stage-B assertion-blind boundary engineering gate."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from evals.e1c_admission import ROOT
from evals.e1c_blind_boundary import BlindBoundaryViolation
from evals.e1c_strict_v5_boundary import AssertionProjectionUnsupported, project_issue
from evals.e1c_strict_v5_runtime import build_bundle, inspect_candidate

OUT = ROOT / "data" / "e1c_strict_v5_stage_b_gate.json"


def build(output: Path = OUT) -> dict:
    checks: dict[str, bool] = {}
    statement = (
        "normalize_value should preserve supported values.\n"
        "def test_hidden():\n"
        "    assert normalize_value(3) == 4\n"
        "The production normalization currently returns an incorrect value."
    )
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        pkg = workspace / "pkg"
        pkg.mkdir()
        (pkg / "engine.py").write_text(
            "def normalize_value(value):\n    return value\n",
            encoding="utf-8",
        )
        tests = workspace / "tests"
        tests.mkdir()
        (tests / "test_engine.py").write_text(
            "def test_hidden():\n    assert normalize_value(3) == 4\n",
            encoding="utf-8",
        )
        projection = project_issue(statement)
        bundle = build_bundle(
            statement=statement,
            workspace=workspace,
            base_commit="a" * 40,
            forbidden_values=("assert normalize_value(3) == 4",),
        )
        checks["inline_assertion_removed"] = "assert normalize_value" not in projection.text
        checks["test_definition_removed"] = "def test_hidden" not in projection.text
        checks["production_candidate_only"] = bool(bundle["candidate_paths"]) and all(
            not path.startswith("tests/") for path in bundle["candidate_paths"]
        )
        try:
            build_bundle(
                statement="Fix normalization. FAIL_TO_PASS contains hidden evaluator data.",
                workspace=workspace,
                base_commit="a" * 40,
            )
        except AssertionProjectionUnsupported:
            checks["evaluator_marker_fail_closed"] = True
        else:
            checks["evaluator_marker_fail_closed"] = False
        try:
            inspect_candidate(bundle, workspace, "tests/test_engine.py")
        except BlindBoundaryViolation:
            checks["test_path_read_rejected"] = True
        else:
            checks["test_path_read_rejected"] = False

    ready = all(checks.values())
    result = {
        "schema": "e1c-strict-v5-stage-b-gate-v1",
        "stage_b_ready": ready,
        "reason": "stage_b_boundary_ready" if ready else "stage_b_boundary_incomplete",
        "checks": checks,
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
