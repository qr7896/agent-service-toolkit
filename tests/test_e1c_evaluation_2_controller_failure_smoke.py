import copy
import hashlib

import pytest

from evals import e1c_evaluation_2_controller_failure_smoke as smoke


def valid():
    result = {'status': 'executed', 'trusted_reproducer': False}
    admission = {'decision': 'EXECUTE_UNCERTIFIED_DEV_CANDIDATE'}
    verdict = {'status': 'controller_qualification_recorded', 'qualification': {'status': 'mechanism_supported_candidate', 'unknown': []},
               'behavior': {'sub_obligation_supported': True}, 'trusted_reproducer': False}
    controls = [{'runs': [{'returncode': 0, 'timed_out': False}]} for _ in range(2)]
    target = {'runs': [{'returncode': 1, 'timed_out': False} for _ in range(2)]}
    return result, admission, verdict, controls, target


def test_synthetic_failure_input_is_separate_and_preserves_source_identity():
    initial = {'issue': 'real', 'public_fixture_facts': [{'real': True}], 'base_commit': 'base', 'windows': []}
    before = copy.deepcopy(initial)
    frozen, payload = smoke.synthetic_input(initial)
    assert initial == before and frozen['base_commit'] == initial['base_commit']
    assert not frozen['public_fixture_facts'] and payload['expected_quote'] in frozen['issue']
    assert frozen['issue_sha256'] == hashlib.sha256(frozen['issue'].encode()).hexdigest()
    assert payload['assertion'] == '' and payload['oracle'] == 'call_completes'


def test_failure_gate_accepts_only_uncertified_complete_branch():
    smoke.validate(*valid())


@pytest.mark.parametrize('mutation', ['trusted', 'unknown', 'target_pass', 'timeout'])
def test_failure_gate_rejects_invalid_branch(mutation):
    result, admission, verdict, controls, target = valid()
    if mutation == 'trusted':
        verdict['trusted_reproducer'] = True
    elif mutation == 'unknown':
        verdict['qualification']['unknown'] = ['missing source']
    elif mutation == 'target_pass':
        target['runs'][1]['returncode'] = 0
    else:
        controls[0]['runs'][0]['timed_out'] = True
    with pytest.raises(ValueError, match='branch gate failed'):
        smoke.validate(result, admission, verdict, controls, target)
