from pathlib import Path

from evals.e1c_strict_v5_probe import (
    candidate_probes,
    docker_probe_command,
    freeze_probe_plan,
    render_probe,
    run_probe,
)


def _localization(tmp_path: Path) -> tuple[Path, dict]:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    source = pkg / "engine.py"
    source.write_text("def normalize_value(value):\n    return value\n", encoding="utf-8")
    import hashlib
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    return tmp_path, {
        "candidates": [{
            "path": "pkg/engine.py",
            "symbol": "normalize_value",
            "start_line": 1,
            "end_line": 2,
            "origin": "issue_ast_definition",
            "depth": 0,
            "source_sha256": digest,
            "read_cost": 45,
            "rank": 1,
            "text": source.read_text(encoding="utf-8"),
        }],
        "candidate_paths": ["pkg/engine.py"],
    }


def test_probe_plan_derives_executable_return_contract_from_prose(tmp_path: Path) -> None:
    _, localization = _localization(tmp_path)
    issue = "normalize_value(3) should return 4 when normalization is enabled."
    probes = candidate_probes(issue, localization)
    assert len(probes) == 1
    assert probes[0]["relation"] == "return_equals"
    assert probes[0]["benchmark_assertion_used"] is False
    assert "assert" not in render_probe(probes[0])
    command = docker_probe_command(probes[0], "swebench/example:latest")
    assert command[0:2] == ["docker", "run"]
    assert "none" in command
    assert "/testbed" in command


def test_probe_plan_rejects_attribute_call_contracts(tmp_path: Path) -> None:
    _, localization = _localization(tmp_path)
    assert candidate_probes("obj.normalize_value(3) should return 4.", localization) == []


def test_probe_plan_abstains_without_safe_contract(tmp_path: Path) -> None:
    _, localization = _localization(tmp_path)
    plan = freeze_probe_plan("Normalization behaves incorrectly in an edge case.", localization)
    assert plan["status"] == "no_reproducer"
    assert plan["trusted_reproducer"] is False


def test_local_execution_detects_failure_but_is_not_trusted_without_network_isolation(tmp_path: Path) -> None:
    workspace, localization = _localization(tmp_path)
    probe = candidate_probes("normalize_value(3) should return 4.", localization)[0]
    result = run_probe(probe, workspace, network_isolated=False)
    assert result["stable"] is True
    assert result["contract_failure_observed"] is True
    assert result["trusted_reproducer"] is False
    assert result["status"] == "reproduced_failure_untrusted_executor"


def test_repeated_probe_generation_is_byte_stable(tmp_path: Path) -> None:
    _, localization = _localization(tmp_path)
    issue = "normalize_value(3) should return 4."
    left = freeze_probe_plan(issue, localization)
    right = freeze_probe_plan(issue, localization)
    assert left == right
