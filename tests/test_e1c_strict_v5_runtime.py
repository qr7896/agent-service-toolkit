from pathlib import Path

import pytest

from evals.e1c_blind_boundary import BlindBoundaryViolation
from evals.e1c_strict_v5_runtime import build_bundle, inspect_candidate, localize


def _workspace(tmp_path: Path) -> Path:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "engine.py").write_text(
        "def normalize_value(value):\n    return value\n\n"
        "def process_value(value):\n    return normalize_value(value)\n",
        encoding="utf-8",
    )
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_engine.py").write_text(
        "def test_hidden():\n    assert normalize_value(3) == 4\n",
        encoding="utf-8",
    )
    return tmp_path


def test_bundle_uses_projection_and_production_only(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    statement = """normalize_value should preserve supported values.
def test_hidden():
    assert normalize_value(3) == 4
The production normalization currently returns an incorrect value.
"""
    bundle = build_bundle(
        statement=statement,
        workspace=workspace,
        base_commit="a" * 40,
        forbidden_values=("assert normalize_value(3) == 4",),
    )
    assert "def test_hidden" not in bundle["issue"]
    assert "assert normalize_value" not in bundle["issue"]
    assert bundle["candidate_paths"]
    assert all(not path.startswith("tests/") for path in bundle["candidate_paths"])


def test_bundle_rejects_evaluator_field_marker(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    with pytest.raises(BlindBoundaryViolation):
        build_bundle(
            statement="Fix normalization. PASS_TO_PASS contains hidden evaluator data.",
            workspace=workspace,
            base_commit="a" * 40,
        )


def test_localization_is_deterministic(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    issue = "normalize_value should preserve supported values and avoid incorrect results."
    left = localize(issue, workspace)
    right = localize(issue, workspace)
    assert left["candidate_paths"] == right["candidate_paths"]
    assert left["localization_sha256"] == right["localization_sha256"]
    assert left["total_read_cost"] == right["total_read_cost"]
    assert left["candidate_count"] <= left["max_candidate_count"]


def test_bundle_hash_is_byte_stable(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    kwargs = {
        "statement": "normalize_value should preserve supported values.",
        "workspace": workspace,
        "base_commit": "c" * 40,
    }
    left = build_bundle(**kwargs)
    right = build_bundle(**kwargs)
    assert left == right
    assert left["bundle_sha256"] == right["bundle_sha256"]


def test_inspect_budget_fails_closed_after_one_call(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    bundle = build_bundle(
        statement="normalize_value should preserve supported values.",
        workspace=workspace,
        base_commit="d" * 40,
    )
    path = bundle["candidate_paths"][0]
    first = inspect_candidate(bundle, workspace, path)
    with pytest.raises(BlindBoundaryViolation, match="budget exceeded"):
        inspect_candidate(bundle, workspace, path, prior_inspections=(first,))


def test_inspect_rejects_unfrozen_test_path(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    bundle = build_bundle(
        statement="normalize_value should preserve supported values.",
        workspace=workspace,
        base_commit="b" * 40,
    )
    with pytest.raises(BlindBoundaryViolation):
        inspect_candidate(bundle, workspace, "tests/test_engine.py")
