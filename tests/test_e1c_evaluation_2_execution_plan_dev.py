from evals import e1c_evaluation_2_execution_plan_dev as runner

PAYLOAD = {"setup_source": "from core import api", "control_action": "api(1)", "target_action": "api(1)", "assertion": ""}


def test_failed_identical_control_requires_normal_configuration_without_edits():
    original = dict(PAYLOAD)
    plan = runner.execution_plan(PAYLOAD, {"status": "control_failed"})
    assert plan["contrast"]["identical_action_AST"]
    assert plan["next_evidence"] == "supported_normal_configuration" and PAYLOAD == original
    assert not plan["trusted_reproducer"] and not plan["controller_modified_probe"]


def test_source_guard_demands_bound_to_own_observed_type_not_report_fact():
    row = {"path": "core.py", "line": 4, "source_sha256": "bound", "predicate": "values"}
    facts = [{"type": "builtins.list"}]
    plan = runner.execution_plan(PAYLOAD, {"status": "target_not_repeatable_failure",
        "matched_public_failure_guards_still_present": [row], "runtime_argument_types": facts})
    assert plan["next_evidence"] == "unexplored_source_consistent_input_hypothesis"
    assert plan["implicit_operations"][0]["source_sha256"] == "bound"
    assert plan["implicit_operations"][0]["possible_protocols"] == ["__bool__", "__len__"]
    assert plan["observed_own_argument_types"] == facts and plan["input_hypothesis_is_not_report_fact"]
    assert not plan["semantic_alignment_proven"]


def test_unknown_operation_does_not_invent_exploration_or_types():
    plan = runner.execution_plan(PAYLOAD, {"status": "target_not_repeatable_failure",
        "matched_public_failure_guards_still_present": [{"predicate": "values is not None"}]})
    assert plan["next_evidence"] == "none" and plan["implicit_operations"] == []
    assert plan["observed_own_argument_types"] == []


def test_successful_candidate_not_demoted_or_promoted_by_diagnostic():
    plan = runner.execution_plan(PAYLOAD, {"status": "base_witness_semantics_unverified"})
    assert plan["next_evidence"] == "none" and not plan["trusted_reproducer"]


def test_wrapper_feedback_preserves_oracle_and_original_candidate(tmp_path, monkeypatch):
    oracle, candidate, execution = {"oracle": "unchanged"}, object(), object()
    monkeypatch.setattr(runner, "_execute", lambda *args: ({"status": "control_failed"}, oracle, candidate, execution))
    result = runner.execute_probe(PAYLOAD, {}, tmp_path, "image", tmp_path, {}, oracle)
    assert result[1:] == (oracle, candidate, execution)
    assert (tmp_path / "execution-plan.json").is_file()
    assert result[0]["next_execution_plan"]["next_evidence"] == "supported_normal_configuration"


def test_scoped_adapter_restores_executor_and_unchanged_caps():
    old = runner._compiled.base.loop.execute_probe
    with runner.configured():
        assert runner._compiled.base.loop.execute_probe is runner.execute_probe
        assert runner._compiled.CAP == 50000 and runner._compiled.TASK_CAP == 24000
    assert runner._compiled.base.loop.execute_probe is old
