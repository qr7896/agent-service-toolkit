import subprocess
import sys

import pytest

from evals.e1c_strict_v7_runner import docker_command, render_call_result, render_python_scenario


def test_render_call_result_is_executable_on_synthetic_module(tmp_path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "engine.py").write_text("def normalize(value):\n    return value + 1\n", encoding="utf-8")
    witness = {
        "kind": "call_result",
        "source": "normalize(3)\n",
        "observable": "return_equals:4",
        "candidate_path": "pkg/engine.py",
    }
    source = render_call_result(witness)
    completed = subprocess.run(
        [sys.executable, "-c", source],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "STRICT_V7_CONTRACT_SATISFIED" in completed.stdout


def test_render_python_scenario_imports_only_frozen_symbols(tmp_path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "engine.py").write_text("def normalize(value):\n    return value + 1\n", encoding="utf-8")
    witness = {
        "kind": "python_scenario",
        "source": "value = normalize(3)\nassert value == 4\n",
        "observable": "scenario_exit_code == 0",
        "candidate_path": "pkg/engine.py",
    }
    source = render_python_scenario(witness, {"normalize": "pkg/engine.py"})
    completed = subprocess.run(
        [sys.executable, "-c", source],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0


def test_docker_command_is_network_disabled() -> None:
    witness = {
        "kind": "call_result",
        "source": "normalize(3)\n",
        "observable": "return_equals:4",
        "candidate_path": "pkg/engine.py",
    }
    command = docker_command(witness, "example/image:tag")
    assert command[:6] == ["docker", "run", "--rm", "--network", "none", "--workdir"]


def test_runner_rejects_unimplemented_state_or_artifact_witnesses() -> None:
    for kind in ("state_transition", "artifact_predicate"):
        with pytest.raises(ValueError):
            docker_command(
                {
                    "kind": kind,
                    "source": "normalize()",
                    "observable": "x",
                    "candidate_path": "pkg/engine.py",
                },
                "example/image:tag",
            )
