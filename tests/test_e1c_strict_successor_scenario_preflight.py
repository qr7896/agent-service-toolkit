import json

from evals.e1c_strict_successor_scenario_preflight import assess, persist

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
COMMAND = ["docker", "run", "--rm", "--network", "none", IMAGE, "python", "-c", "pass"]


def result(**overrides):
    args = dict(
        witness=WITNESS,
        expected_base_commit=BASE,
        observed_base_commit=BASE,
        image_digest=IMAGE,
        command=COMMAND,
        returncode=0,
        timed_out=False,
        stdout_sha256="c" * 64,
        stderr_sha256="d" * 64,
    )
    args.update(overrides)
    return assess(**args)


def test_promotes_only_successful_exact_base_network_disabled_scenario():
    value = result()
    assert value["execution_ready"] is True
    assert value["promotion_reason"] == "preflight_pass"
    assert value["provider_calls"] == 0
    assert value["expected_base_commit"] == BASE
    assert value["observed_base_commit"] == BASE
    assert value["image_digest"] == IMAGE
    assert value["command"] == COMMAND
    assert value["observable"] == "scenario_exit_code == 0"
    assert value["candidate_path"] == "pkg/engine.py"


def test_nonzero_timeout_or_base_mismatch_fail_closed():
    assert result(returncode=1)["execution_ready"] is False
    assert result(returncode=None, timed_out=True)["execution_ready"] is False
    assert result(observed_base_commit="e" * 40)["execution_ready"] is False


def test_mutable_image_or_network_enabled_fail_closed():
    assert result(image_digest="example/image:latest")["execution_ready"] is False
    command = ["docker", "run", "--rm", "example/image", "python", "-c", "pass"]
    assert result(command=command)["execution_ready"] is False


def test_benchmark_identity_or_assertion_is_rejected():
    bad = dict(WITNESS, benchmark_assertion_used=True)
    assert result(witness=bad)["execution_ready"] is False
    bad = dict(WITNESS, task_id_used=True)
    assert result(witness=bad)["execution_ready"] is False


def test_unsupported_observable_does_not_promote():
    bad = dict(WITNESS, observable="stdout contains ok")
    assert result(witness=bad)["execution_ready"] is False


def test_persist_writes_canonical_artifact(tmp_path):
    value = result()
    target = tmp_path / "preflight.json"
    file_sha = persist(value, target)
    loaded = json.loads(target.read_text(encoding="utf-8"))
    assert loaded == value
    assert len(file_sha) == 64
