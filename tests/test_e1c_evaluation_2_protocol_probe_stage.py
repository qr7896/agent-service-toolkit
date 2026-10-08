import pytest

from evals import e1c_evaluation_2_protocol_probe_stage as stage


def test_stage_nested_budget_decoder_and_input_hooks_restore():
    compiled = stage.pilot.previous.previous.method.base.base._compiled
    before = compiled.inputs, compiled.preflight, stage.pilot.BATCH_CAP, stage.pilot.limited_invoke
    with stage.configured(), compiled.configured():
        assert compiled.CAP == 40000 and compiled.TASK_CAP == 24000
        assert compiled.preflight is stage.preflight
        assert compiled.base.loop.parse_action is stage.pilot.parse_action
        assert compiled.base.loop.execute_probe is stage.pilot.previous.adapter.execute_probe
        assert stage.pilot.limited_invoke is stage.limited_invoke
    assert before == (compiled.inputs, compiled.preflight, stage.pilot.BATCH_CAP, stage.pilot.limited_invoke)


@pytest.mark.asyncio
async def test_stage_actual_gateway_has_three_call_limit_without_mutation():
    config = {'configurable': {'provider_max_calls_per_task': 4}}

    async def original(model, messages, bounded, **kwargs):
        assert bounded['configurable']['provider_max_calls_per_task'] == 3
        return 'bounded'

    assert await stage.limited_invoke(original, None, [], config) == 'bounded'
    assert config['configurable']['provider_max_calls_per_task'] == 4
