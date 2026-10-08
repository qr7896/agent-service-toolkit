import json

import pytest

from evals import e1c_evaluation_2_three_arm_boundary_dev as method
from evals import e1c_evaluation_2_three_arm_dev as parent


def test_augment_shares_equal_source_not_mutable_lists_and_keeps_strict_test_boundary():
    frozen = {'issue': 'public', 'base_commit': 'a' * 40,
              'windows': [{'path': 'module.py', 'start_line': 1, 'end_line': 2, 'text': 'def f():\n    return G'}]}
    bodies = parent.arm_payloads(frozen, {'windows': [{'text': 'BASE_ASSERTION'}]}, {'full_issue_trusted': False})
    extra = {'path': 'module.py', 'text': 'G = 1'}
    result = method.augment_bodies(bodies, [extra], [{'id': 'own-counterexample', 'synthetic': True}])
    assert all(len(b['production_windows']) == 2 for b in result.values())
    assert all(len(b['production_windows']) == 1 for b in bodies.values())
    assert 'conditional_evidence' not in result['standard']
    assert 'base_tests' not in result['strict_evidence']
    assert 'BASE_ASSERTION' not in parent._prompt_text(parent.messages(result['strict_evidence']))
    assert result['strict_evidence']['conditional_evidence']['full_issue_trusted'] is False
    assert result['standard_evidence']['conditional_evidence'] == result['strict_evidence']['conditional_evidence']


def test_global_retrieval_reads_only_base_assignment_used_by_exposed_complete_function(monkeypatch, tmp_path):
    raw = b'G = 1\nUNUSED = 2\ndef f():\n    return G\n'
    observed = []

    def blob(workspace, base, name):
        observed.append((workspace, base, name))
        return raw

    monkeypatch.setattr(parent.source.method.qualified, 'git_blob', blob)
    windows = [{'path': 'module.py', 'start_line': 3, 'end_line': 4, 'source_sha256': 'bound-source'}]
    result = method.loaded_globals(windows, tmp_path, 'a' * 40)
    assert observed == [(tmp_path, 'a' * 40, 'module.py')]
    assert len(result) == 1 and result[0]['text'] == 'G = 1'
    assert result[0]['origin'] == 'base_bound_loaded_global_assignment'
    assert result[0]['source_sha256'] == 'bound-source'


def test_conditional_global_rebinding_context_is_kept_not_declared_a_runtime_value(monkeypatch, tmp_path):
    raw = b'AVAILABLE = True\ntry:\n    import optional\nexcept ImportError:\n    AVAILABLE = False\ndef f():\n    return AVAILABLE\n'
    monkeypatch.setattr(parent.source.method.qualified, 'git_blob', lambda *args: raw)
    windows = [{'path': 'module.py', 'start_line': 6, 'end_line': 7, 'source_sha256': 'bound-source'}]
    result = method.loaded_globals(windows, tmp_path, 'a' * 40)
    assert len(result) == 1 and 'except ImportError:' in result[0]['text']
    assert result[0]['binding_may_be_reassigned'] is True
    assert result[0]['binding_context_complete'] is True
    assert result[0]['runtime_value_certified'] is False


def test_counterexample_selection_uses_only_public_base_and_release_records(tmp_path):
    base, old = [], []
    for n in range(6):
        (tmp_path / f'own{n}.py').write_text('PUBLIC_OWN_SOURCE', encoding='utf-8')
        base.append({'id': f'own{n}', 'returncode': 1, 'stderr': 'own runtime failure'})
        old.append({'id': f'own{n}', 'returncode': 0})
    examples = method.counterexamples(base, old, tmp_path)
    assert [r['id'] for r in examples] == ['own0', 'own1', 'own4', 'own5']
    assert all(r['synthetic_hypothesis_not_reported_input'] for r in examples)
    assert all(r['probe_source'] == 'PUBLIC_OWN_SOURCE' for r in examples)


@pytest.mark.parametrize('wrapped', [False, True])
def test_new_compile_hook_normalizes_only_envelope_and_keeps_edit_bytes(monkeypatch, wrapped):
    edits = [{'path': 'module.py', 'old': 'x = 1', 'new': 'x = 2'}]
    value = {'edits': edits}
    if wrapped:
        value['type'] = 'json_object'
    monkeypatch.setattr(method, '_compile', lambda raw, body, root: json.loads(raw))
    assert method.compile_patch(json.dumps(value), {}, None) == {'edits': edits}


def test_scoped_configuration_reuses_generator_scorer_and_restores_original_identity():
    original = (parent.OUT, parent.SYSTEM, parent.inputs, parent.preflight, parent.compile_patch)
    with method.configured():
        assert parent.OUT == method.OUT and parent.RUN_ID == method.RUN_ID
        assert parent.inputs is method.inputs and parent.preflight is method.preflight
        assert parent.compile_patch is method.compile_patch
        assert 'ONLY the key edits' in parent.SYSTEM
        assert parent.TOTAL_TOKENS == 48_000 and parent.CELL_TOKENS == 16_000
    assert (parent.OUT, parent.SYSTEM, parent.inputs, parent.preflight, parent.compile_patch) == original
