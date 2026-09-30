from evals.e1c_strict_v7_probe import freeze_typed_plan, typed_candidates


def _loc(symbol="normalize", path="pkg/engine.py"):
    return {
        "candidates": [
            {
                "path": path,
                "symbol": symbol,
                "source_sha256": "a" * 64,
                "text": f"def {symbol}(value=None):\n    return value\n",
            }
        ]
    }


def test_v7_keeps_v6_literal_relation_as_executable_candidate() -> None:
    plan = freeze_typed_plan("normalize(3) should return 4.", _loc())
    assert plan["status"] == "candidate_executable_witnesses"
    assert plan["executable_candidate_count"] == 1


def test_v7_extracts_safe_python_scenario_from_public_issue_fence() -> None:
    issue = """Reproduce with:\n```python\nvalue = normalize(3)\nassert value == 4\n```\n"""
    rows = typed_candidates(issue, _loc())
    scenario = [row for row in rows if row["freeze"].get("witness", {}).get("kind") == "python_scenario"]
    assert len(scenario) == 1
    assert scenario[0]["execution_ready"] is True


def test_v7_extracts_indented_python_scenario() -> None:
    issue = """Reproduce with:\n    value = normalize(3)\n    assert value == 4\nThen continue."""
    rows = typed_candidates(issue, _loc())
    scenario = [row for row in rows if row["freeze"].get("witness", {}).get("kind") == "python_scenario"]
    assert len(scenario) == 1
    assert scenario[0]["execution_ready"] is True


def test_v7_marks_scenario_nonexecuting_when_external_names_are_unresolved() -> None:
    issue = """```python\nvalue = normalize(OtherModel())\nassert value == 4\n```"""
    rows = typed_candidates(issue, _loc())
    scenario = [row for row in rows if row["freeze"].get("witness", {}).get("kind") == "python_scenario"]
    assert len(scenario) == 1
    assert scenario[0]["execution_ready"] is False


def test_v7_rejects_unsafe_python_scenario() -> None:
    issue = """```python\nimport requests\nrequests.get('https://example.com')\nnormalize(3)\n```"""
    rows = typed_candidates(issue, _loc())
    assert not [row for row in rows if row["freeze"].get("witness", {}).get("kind") == "python_scenario"]


def test_v7_extracts_state_transition_but_does_not_pretend_it_is_executable() -> None:
    issue = "normalize() should clear the lookup cache."
    rows = typed_candidates(issue, _loc())
    state = [row for row in rows if row["freeze"].get("witness", {}).get("kind") == "state_transition"]
    assert len(state) == 1
    assert state[0]["execution_ready"] is False


def test_v7_extracts_single_safe_local_artifact_command_as_nonexecuting_candidate() -> None:
    issue = """Run locally:\n```console\n$ python -m sphinx -b html docs build/html\n```"""
    rows = typed_candidates(issue, _loc(path="sphinx/application.py"))
    artifact = [row for row in rows if row["freeze"].get("witness", {}).get("kind") == "artifact_predicate"]
    assert len(artifact) == 1
    assert artifact[0]["execution_ready"] is False


def test_v7_does_not_associate_python_scenario_without_unique_symbol_evidence() -> None:
    issue = """```python\nvalue = unrelated(3)\nassert value == 4\n```"""
    rows = typed_candidates(issue, _loc())
    assert rows == []
