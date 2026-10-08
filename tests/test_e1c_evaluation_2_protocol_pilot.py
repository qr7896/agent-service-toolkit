import json

import pytest

from evals import e1c_evaluation_2_protocol_pilot as pilot


def test_selection_is_fixed_library_order_not_file_map():
    rows = [({'instance_id': name}, {}, None) for name in
            ('scikit-learn__a', 'scikit-learn__b', 'marshmallow-code__a', 'marshmallow-code__b')]
    assert [r[0]['instance_id'] for r in pilot.select_inputs(rows)] == ['scikit-learn__a', 'marshmallow-code__a']
    with pytest.raises(ValueError):
        pilot.select_inputs(rows[:2])


def test_actual_nested_runner_hooks_are_restored():
    compiled = pilot.previous.previous.method.base.base._compiled
    before = compiled.CAP, compiled.inputs, compiled.parse_action, compiled.configured, pilot.previous.adapter.POLICY
    with pilot.configured(), compiled.configured():
        assert compiled.CAP == 20000 and compiled.TASK_CAP == 12000
        assert compiled.base.loop.parse_action is pilot.parse_action
        assert compiled.base.loop.messages is pilot.previous.adapter.messages
        assert compiled.base.loop.execute_probe is pilot.previous.adapter.execute_probe
        assert compiled.conversation is pilot.previous.adapter.conversation
        assert 'production imports and fixture' not in pilot.previous.adapter.POLICY
        assert compiled.preflight is pilot.preflight
    assert before == (compiled.CAP, compiled.inputs, compiled.parse_action, compiled.configured, pilot.previous.adapter.POLICY)


def test_real_parser_routes_wrapper_to_strict_code_and_proof():
    token = pilot.codec._issue.set('The previous release completes without raising.\n')
    proof = pilot.codec._codec_proof.set(None)
    fields = {'issue_quote_ref': 0, 'expected_quote_ref': 0, 'oracle': 'call_completes',
              'setup_source': 'from core import Api', 'control_action': 'Api()', 'target_action': 'Api(flag=True)', 'assertion': ''}
    try:
        action, value = pilot.parse_action(json.dumps({'type': 'json_object', 'action': {'probe': fields}}))
        assert action == 'probe' and value['target_action'] == 'Api(flag=True)'
        assert pilot.codec._codec_proof.get()['references'] is not None
        with pytest.raises((ValueError, SyntaxError)):
            pilot.parse_action(json.dumps({'probe': {**fields, 'setup_source': 'production imports and fixture'}}))
        assert pilot.codec._codec_proof.get() is None
    finally:
        pilot.codec._issue.reset(token)
        pilot.codec._codec_proof.reset(proof)


@pytest.mark.asyncio
async def test_actual_budget_gateway_limits_calls_without_mutating_config():
    config = {'configurable': {'provider_max_calls_per_task': 4, 'provider_total_token_ceiling': 15000}}

    async def original(model, messages, bounded, **kwargs):
        assert bounded['configurable']['provider_max_calls_per_task'] == 1
        assert bounded['configurable']['provider_total_token_ceiling'] == 15000
        return 'actual gateway'

    assert await pilot.limited_invoke(original, None, [], config, role='pilot') == 'actual gateway'
    assert config['configurable']['provider_max_calls_per_task'] == 4
