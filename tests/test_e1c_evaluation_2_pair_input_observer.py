import ast

import numpy as np
import pytest

from evals import e1c_evaluation_2_pair_input_observer as observer

namespace = {}
exec(observer.FINGERPRINT, namespace)
fingerprint = namespace['fingerprint']


def test_bool_int_and_container_types_not_conflated():
    assert fingerprint(True)['sha256'] != fingerprint(1)['sha256']
    assert fingerprint([1, 2])['sha256'] != fingerprint((1, 2))['sha256']
    assert fingerprint({'a': 1, 'b': 2}) == fingerprint({'b': 2, 'a': 1})


def test_numpy_typed_bytes_shape_dtype_and_content_are_bound():
    a = np.array(['first', 'second'])
    assert fingerprint(a, np) == fingerprint(a.copy(), np)
    assert fingerprint(a, np)['sha256'] != fingerprint(a[::-1], np)['sha256']
    assert fingerprint(np.array([1, 2], dtype='int32'), np)['sha256'] != fingerprint(np.array([1, 2], dtype='int64'), np)['sha256']
    assert fingerprint(np.array([1, 2]), np)['sha256'] != fingerprint(np.array([[1, 2]]), np)['sha256']


@pytest.mark.parametrize('value', [np.array([object()], dtype=object), np.zeros(100000), float('nan'), [1] * 65])
def test_unsupported_or_budget_exceeded_values_stay_unknown(value):
    assert fingerprint(value, np)['status'] == 'unknown'


def test_unknown_objects_and_subclasses_do_not_invoke_user_methods():
    class Trap:
        def __repr__(self):
            raise AssertionError('repr forbidden')

        def __getattribute__(self, name):
            raise AssertionError('object attribute access forbidden')

    class Array(np.ndarray):
        def tobytes(self, *args, **kwargs):
            raise AssertionError('subclass method forbidden')

    assert fingerprint(Trap(), np)['status'] == 'unknown'
    assert fingerprint(np.array([1]).view(Array), np)['status'] == 'unknown'
    loop = []
    loop.append(loop)
    assert fingerprint(loop)['status'] == 'unknown'


def test_call_spec_uses_frozen_top_level_call_and_rejects_side_effects():
    source = 'from core import alpha as f\nf(obj, option=names, depth=4)\n'
    spec = observer.call_spec(source, 'alpha', ['option', 'depth'])
    assert spec['line'] == 2 and spec['parameters']['option'] == {'kind': 'name', 'name': 'names'}
    assert spec['parameters']['depth'] == {'kind': 'literal', 'value': 4}
    with pytest.raises(ValueError, match='side-effect-free'):
        observer.call_spec(source.replace('depth=4', 'depth=other()'), 'alpha', ['option'])
    with pytest.raises(ValueError, match='unique'):
        observer.call_spec(source + 'f(obj, option=names, depth=4)\n', 'alpha', ['option'])


def test_shared_keywords_can_match_while_receiver_is_unknown():
    record = {'parameters': {'option': fingerprint(np.array(['a', 'b']), np), 'depth': fingerprint(4), 'positional_0': fingerprint(object())}}
    result = observer.compare_inputs({'returncode': 0, 'records': [record]}, {'returncode': 1, 'records': [record]}, ['option', 'depth'])
    assert result['shared_keyword_values_match'] and not result['all_inputs_match']
    assert not result['trusted_reproducer'] and not result['public_fixture_value_equivalence_proven']
    changed = {'parameters': {**record['parameters'], 'depth': fingerprint(5)}}
    assert not observer.compare_inputs({'returncode': 0, 'records': [record]}, {'returncode': 1, 'records': [changed]}, ['depth'])['shared_keyword_values_match']


def test_missing_snapshot_or_invalid_execution_does_not_match():
    assert not observer.compare_inputs({'returncode': 0, 'records': []}, {'returncode': 1, 'records': []}, ['x'])['shared_keyword_values_match']
    assert observer.compare_inputs({'returncode': 125}, {'returncode': 1}, ['x'])['status'] == 'unknown_normal_or_target_outcome'


def test_driver_binds_probe_and_canonical_source_without_evaluating_arguments():
    spec = observer.call_spec('from core import alpha\nalpha(option=x)\n', 'alpha', ['option'])
    source, _ = observer.build_driver('a' * 64, [{'path': 'core.py', 'line': 1, 'variable': 'option', 'source_sha256': 'b' * 64}],
                                     'c' * 32, spec, 'd' * 40)
    ast.parse(source)
    assert 'live != canonical' in source and 'before_call_not_function_body' in source
    assert 'eval(' not in source and 'repr(' not in source and 'getattr(' not in source
