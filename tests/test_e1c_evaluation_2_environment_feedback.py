import copy

import pytest

from evals import e1c_evaluation_2_acquisition_context as messages
from evals.e1c_evaluation_2_environment_feedback import project_environment


def record():
    return {'schema': 'e1c-evaluation-2-probe-execution-v1', 'input_sha256': 'i', 'image': 'image', 'base_commit': 'base',
            'missing_optional_import': 'dateutil', 'network_none': True, 'pull_never': True,
            'runs': [{'returncode': 0, 'timed_out': False}]}


def test_projection_is_own_condition_not_natural_environment_or_semantic_certificate():
    original = {'status': 'evidence_required_before_selection'}
    before = copy.deepcopy(original)
    value = project_environment(original, [record(), record()], record())
    projected = messages.compact_feedback(value)['own_executor_environment']
    assert projected['condition'] == 'executor_forced_import_failure_in_both_phases'
    assert not projected['naturally_uninstalled_claimed'] and not projected['trusted_reproducer']
    assert original == before


@pytest.mark.parametrize('key,value', [('base_commit', 'different'), ('network_none', False),
                                     ('missing_optional_import', None), ('missing_optional_import', 'unsafe.module')])
def test_mismatched_or_missing_conditions_are_not_invented(key, value):
    other = {**record(), key: value}
    with pytest.raises(ValueError):
        project_environment({}, [record(), other], record())
