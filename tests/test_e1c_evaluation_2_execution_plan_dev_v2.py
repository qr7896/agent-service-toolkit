from evals import e1c_evaluation_2_execution_plan_dev_v2 as runner


def test_actual_inner_runner_configuration_preserves_full_plan_hook():
    compiled = runner.base._compiled
    before = compiled.execute_probe, compiled.base.loop.execute_probe
    with runner.configured():
        with compiled.configured():
            assert compiled.base.loop.execute_probe is runner.base.execute_probe
            assert compiled.execute_probe is runner.base.execute_probe
            assert compiled.CAP == 50000 and compiled.TASK_CAP == 24000
    assert (compiled.execute_probe, compiled.base.loop.execute_probe) == before


def test_nested_configuration_exception_restores_owners():
    compiled = runner.base._compiled
    before = compiled.execute_probe, compiled.base.loop.execute_probe
    try:
        with runner.configured():
            with compiled.configured():
                raise RuntimeError("synthetic failure")
    except RuntimeError:
        pass
    assert (compiled.execute_probe, compiled.base.loop.execute_probe) == before


def test_namespace_and_method_bind_v1_negative_without_modifying_it():
    assert runner.OUT.name == "execution-plan-reference-dev-v2"
    assert "evals/e1c_evaluation_2_execution_plan_dev.py" in runner.MODULES
    assert runner.base.OUT.name == "execution-plan-reference-dev-v1"
