from evals.e1c_strict_v7_witness_ir import WitnessIR, freeze, validate


def _witness(**changes) -> WitnessIR:
    base = {
        "kind": "python_scenario",
        "source": "value = 1\nassert value == 1\n",
        "observable": "exit_code == 0",
        "candidate_path": "pkg/engine.py",
    }
    base.update(changes)
    return WitnessIR(**base)


def test_v7_accepts_bounded_synthetic_python_scenario() -> None:
    result = freeze(_witness())
    assert result["status"] == "candidate"
    assert result["witness"]["benchmark_assertion_used"] is False


def test_v7_rejects_test_paths() -> None:
    safe, reason = validate(_witness(candidate_path="tests/test_engine.py"))
    assert safe is False
    assert reason == "non_production_candidate_path"


def test_v7_rejects_network_and_dynamic_python() -> None:
    assert freeze(_witness(source="import requests\nrequests.get('https://x')"))["status"] == "rejected"
    assert freeze(_witness(source="eval('1+1')"))["status"] == "rejected"


def test_v7_rejects_benchmark_assertion_or_task_identity() -> None:
    assert freeze(_witness(benchmark_assertion_used=True))["status"] == "rejected"
    assert freeze(_witness(task_id_used=True))["status"] == "rejected"


def test_v7_artifact_command_is_single_process_and_network_free() -> None:
    good = WitnessIR(
        kind="artifact_predicate",
        source="python -m sphinx -b html docs build/html",
        observable="artifact selector contains expected local target",
        candidate_path="sphinx/application.py",
    )
    bad = WitnessIR(
        kind="artifact_predicate",
        source="git clone https://example.com/repro && make html",
        observable="artifact exists",
        candidate_path="sphinx/application.py",
    )
    assert freeze(good)["status"] == "candidate"
    assert freeze(bad)["status"] == "rejected"
