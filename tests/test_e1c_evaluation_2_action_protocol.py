import copy
import json

import pytest

from evals import e1c_evaluation_2_action_protocol as protocol


def test_policy_has_no_code_bearing_example_values_and_keeps_boundaries():
    value = protocol.policy()
    assert 'production imports and fixture' not in value and 'normal API call"' not in value
    for term in ('Never access existing tests', 'Unknowns remain unknown', 'remain locked', 'No network', 'empty assertion'):
        # The lock text uses "stay locked" in the original policy.
        expected = 'stay locked' if term == 'remain locked' else term
        assert expected in value
    assert 'ACTUAL executable Python' in value


def test_exact_transport_wrapper_preserves_all_inner_values():
    inner = {'retrieve': 'Schema'}
    wrapped = {'type': 'json_object', 'action': inner}
    before = copy.deepcopy(wrapped)
    assert protocol.unwrap_action(wrapped) == inner and wrapped == before


@pytest.mark.parametrize('value', [{'type': 'other', 'action': {'retrieve': 'Schema'}},
                                  {'type': 'json_object', 'action': 'code'},
                                  {'type': 'json_object', 'action': {'retrieve': 'Schema', 'other': True}},
                                  {'type': 'json_object', 'action': {'shell': 'anything'}}])
def test_unknown_wrapper_never_guessed(value):
    assert protocol.unwrap_action(value) == value


def test_existing_decoder_checks_actual_code_not_schema_description():
    issue = 'The previous release works without raising.\n'
    fields = {'issue_quote_ref': 0, 'expected_quote_ref': 0, 'oracle': 'call_completes', 'setup_source': 'from core import Api',
              'control_action': 'Api()', 'target_action': 'Api(flag=True)', 'assertion': ''}
    action, actual, _ = protocol.decode(json.dumps({'type': 'json_object', 'action': {'probe': fields}}), issue)
    assert action == 'probe' and actual['setup_source'] == fields['setup_source']
    with pytest.raises((ValueError, SyntaxError)):
        protocol.decode(json.dumps({'probe': {**fields, 'setup_source': 'production imports and fixture'}}), issue)
