from pathlib import Path

from evals.e1c_strict_v6_probe import docker_witness_command, render_witness
from evals.e1c_strict_v6_runtime import build_bundle


def _workspace(tmp_path: Path) -> Path:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "engine.py").write_text(
        "def normalize(value):\n    return value\n",
        encoding="utf-8",
    )
    return tmp_path


def test_v6_bundle_builds_behavioral_witness_from_projected_prose(tmp_path: Path) -> None:
    bundle = build_bundle(
        statement="normalize(3) currently returns 3 instead of 4.",
        workspace=_workspace(tmp_path),
        base_commit="a" * 40,
    )
    plan = bundle["witness_plan"]
    assert plan["status"] == "candidate_executable_witnesses"
    witness = plan["witnesses"][0]
    source = render_witness(witness)
    assert "STRICT_V6_CONTRACT_MISMATCH" in source
    assert "assert " not in source
    command = docker_witness_command(witness, "swebench/example:latest")
    assert command[:4] == ["docker", "run", "--rm", "--network"]
    assert "none" in command


def test_v6_bundle_is_deterministic(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    kwargs = {
        "statement": "normalize('x') should contain 'x'.",
        "workspace": workspace,
        "base_commit": "b" * 40,
    }
    assert build_bundle(**kwargs) == build_bundle(**kwargs)
