import copy
import hashlib

import pytest

from evals import e1c_evaluation_2_behavior_gate as gate


def fixture(tmp_path, monkeypatch, owner='Api', parameter='flag', signature='count=1'):
    raw = f'class {owner}:\n    def __init__(self, {signature}):\n        pass\n'.encode()
    (tmp_path / 'core.py').write_bytes(raw)
    monkeypatch.setattr(gate, 'git_blob', lambda *args: raw)
    quote = f'Please expose `{parameter}` in `core.{owner}.__init__()`.\n'
    frozen = {'issue': quote + f'{parameter} : bool, optional\n', 'base_commit': 'b' * 40,
              'windows': [{'path': 'core.py', 'source_sha256': hashlib.sha256(raw).hexdigest()}]}
    payload = {'setup_source': f'from core import {owner}', 'target_action': f'{owner}(count=1, {parameter}=True)',
               'control_action': f'{owner}(count=1)', 'expected_quote': quote, 'oracle': 'call_completes', 'assertion': ''}
    source = payload['setup_source'] + '\n' + payload['target_action'] + '\n'
    candidate = {'source': source, 'probe_sha256': hashlib.sha256(source.encode()).hexdigest()}
    observation = {'schema': 'e1c2-source-bound-exception-observation-v2', 'original_probe_sha256': candidate['probe_sha256'],
                   'canonical_git_and_effective_file_hash_required': True, 'returncode': 1,
                   'records': [{'scope': 'owned_probe', 'path': '/e1c2_model_probe.py', 'line': 2,
                                'exception_type': 'builtins.TypeError', 'declared_missing_keyword': parameter}]}
    qualification = {'status': 'mechanism_supported_candidate', 'rejected': [], 'unknown': []}
    return payload, frozen, tmp_path, candidate, observation, qualification


@pytest.mark.parametrize('owner,parameter', [('Api', 'flag'), ('Client', 'cache'), ('Engine', 'resume')])
def test_generic_explicit_request_supports_only_sub_obligation(tmp_path, monkeypatch, owner, parameter):
    args = fixture(tmp_path, monkeypatch, owner, parameter)
    before = copy.deepcopy(args[:2])
    value = gate.assess(*args, documentation={'status': 'documentation_scope_gap'})
    assert value['status'] == 'supported_boolean_keyword_subobligation' and value['sub_obligation_supported']
    assert not value['trusted_reproducer'] and not value['full_issue_obligations_verified']
    assert value['public_change_request_overrides_base_documentation']
    assert args[:2] == before


@pytest.mark.parametrize('field,value', [('line', 3), ('declared_missing_keyword', 'other'), ('exception_type', 'builtins.ValueError')])
def test_wrong_error_location_parameter_or_type_not_supported(tmp_path, monkeypatch, field, value):
    args = fixture(tmp_path, monkeypatch)
    args[4]['records'][0][field] = value
    assert not gate.assess(*args)['sub_obligation_supported']


def test_wrong_module_same_class_name_not_matched(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch)
    args[1]['issue'] = args[1]['issue'].replace('core.Api', 'foreign.Api')
    args[0]['expected_quote'] = args[0]['expected_quote'].replace('core.Api', 'foreign.Api')
    assert not gate.assess(*args)['sub_obligation_supported']


def test_normal_control_must_differ_only_by_requested_keyword(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch)
    args[0]['control_action'] = 'Api(count=2)'
    assert 'normal_differs_beyond_requested_keyword' in gate.assess(*args)['reasons']


@pytest.mark.parametrize('signature', ['count=1, **kwargs', 'count=1, flag=False'])
def test_source_signature_already_accepting_keyword_does_not_support_missing_binding(tmp_path, monkeypatch, signature):
    assert not gate.assess(*fixture(tmp_path, monkeypatch, signature=signature))['sub_obligation_supported']


def test_compiled_probe_with_other_parameter_value_not_equivalent(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch)
    candidate = args[3]
    candidate['source'] = candidate['source'].replace('flag=True', 'flag=False')
    candidate['probe_sha256'] = hashlib.sha256(candidate['source'].encode()).hexdigest()
    args[4]['original_probe_sha256'] = candidate['probe_sha256']
    assert 'original_probe_constructor_differs_from_payload' in gate.assess(*args)['reasons']


def test_unbound_observation_or_rejected_program_not_promoted(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch)
    args[4]['original_probe_sha256'] = 'other'
    assert gate.assess(*args)['status'] == 'rejected_observation_binding'
    args[5]['rejected'] = ['import_alias_shadowed']
    assert gate.assess(*args)['status'] == 'rejected_program_evidence'


def test_source_base_change_fails_closed(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(gate, 'git_blob', lambda *args: b'changed base')
    with pytest.raises(ValueError, match='frozen/base identity'):
        gate.assess(*args)


def test_missing_public_boolean_domain_not_inferred(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch)
    args[1]['issue'] = args[0]['expected_quote']
    assert 'public_boolean_parameter_domain_unproven' in gate.assess(*args)['reasons']


def test_comparative_report_shared_values_and_source_docs_not_global_trust(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch)
    quote = 'This works for\n'
    args[1]['issue'] = quote + 'tree.alpha(model, names=labels)\nbut not for\ntree.beta(model, names=labels)\n'
    args[0]['expected_quote'] = quote
    value = gate.assess(*args, pair={'shared_keyword_values_match': True, 'all_inputs_match': False},
                        documentation={'status': 'documentation_scope_gap'})
    assert value['status'] == 'conditional_comparative_hypothesis' and not value['sub_obligation_supported']
    assert 'receiver_or_other_input_state_unproven' in value['reasons']
    assert 'observed_input_type_not_explicitly_documented' in value['reasons']


def test_regression_quote_is_not_proven_version_oracle(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch)
    quote = 'This worked in previous releases without raising.\n'
    args[1]['issue'] = quote
    args[0]['expected_quote'] = quote
    assert gate.assess(*args)['status'] == 'conditional_regression_hypothesis'
