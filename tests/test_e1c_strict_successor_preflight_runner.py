import subprocess
from pathlib import Path
from types import SimpleNamespace

from evals.e1c_strict_successor_preflight_runner import run_preflight

WITNESS = {
    "kind": "python_scenario",
    "source": "value = normalize(3)\nprint(value)\n",
    "observable": "scenario_exit_code == 0",
    "candidate_path": "pkg/engine.py",
    "provenance": "projected_issue_plus_production_localization",
    "benchmark_assertion_used": False,
    "task_id_used": False,
}
BASE = "a" * 40
IMAGE = "example/image@sha256:" + "b" * 64


def test_runner_persists_successful_exact_base_preflight(monkeypatch, tmp_path):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[0] == "git":
            return SimpleNamespace(returncode=0, stdout=BASE + "\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="ok\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    target = tmp_path / "preflight.json"
    value = run_preflight(
        WITNESS,
        source_root=Path("repo"),
        expected_base_commit=BASE,
        image_digest=IMAGE,
        artifact_path=target,
        import_map={"normalize": "pkg/engine.py"},
        timeout_seconds=30,
    )
    assert value["execution_ready"] is True
    assert target.exists()
    assert calls[1][:6] == ["docker", "run", "--rm", "--network", "none", "--workdir"]


def test_runner_timeout_fails_closed(monkeypatch, tmp_path):
    def fake_run(command, **kwargs):
        if command[0] == "git":
            return SimpleNamespace(returncode=0, stdout=BASE + "\n", stderr="")
        raise subprocess.TimeoutExpired(command, kwargs["timeout"], output="partial", stderr="late")

    monkeypatch.setattr(subprocess, "run", fake_run)
    value = run_preflight(
        WITNESS,
        source_root=Path("repo"),
        expected_base_commit=BASE,
        image_digest=IMAGE,
        artifact_path=tmp_path / "timeout.json",
    )
    assert value["execution_ready"] is False
    assert value["timed_out"] is True


def test_runner_base_mismatch_fails_closed(monkeypatch, tmp_path):
    def fake_run(command, **kwargs):
        if command[0] == "git":
            return SimpleNamespace(returncode=0, stdout="c" * 40 + "\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    value = run_preflight(
        WITNESS,
        source_root=Path("repo"),
        expected_base_commit=BASE,
        image_digest=IMAGE,
        artifact_path=tmp_path / "mismatch.json",
    )
    assert value["execution_ready"] is False
    assert value["exact_base_identity"] is False


def test_runner_rejects_unbounded_timeout(tmp_path):
    try:
        run_preflight(
            WITNESS,
            source_root=Path("repo"),
            expected_base_commit=BASE,
            image_digest=IMAGE,
            artifact_path=tmp_path / "x.json",
            timeout_seconds=121,
        )
    except ValueError as exc:
        assert "1..120" in str(exc)
    else:
        raise AssertionError("expected bounded-timeout rejection")
