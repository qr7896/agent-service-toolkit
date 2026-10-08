import copy
import hashlib

import pytest

from evals import e1c_evaluation_2_scoped_controller as scoped


def fixture(tmp_path, monkeypatch):
    source = (b'class First:\n    def __init__(self, count=1):\n        """Parameters\n        ----------\n        count : int\n        Examples\n        --------\n        assert answer == 99\n        """\n        pass\n'
              b'class Second:\n    def __init__(self, other=1):\n        """Parameters\n        ----------\n        other : str\n        """\n        pass\n')
    (tmp_path / 'core.py').write_bytes(source)
    monkeypatch.setattr(scoped.base, 'git_blob', lambda *args: source)
    return {'base_commit': 'b' * 40, 'windows': [{'path': 'core.py', 'symbol': '__init__', 'start_line': 2,
                                               'source_sha256': hashlib.sha256(source).hexdigest()}]}


def verdict():
    return {'qualification': {'status': 'mechanism_supported_candidate', 'unknown': [], 'rejected': []},
            'behavior': {'status': 'supported_boolean_keyword_subobligation', 'sub_obligation_supported': True},
            'trusted_reproducer': False}


def test_unique_header_infers_actual_owner_and_excludes_same_name_sibling(tmp_path, monkeypatch):
    frozen = fixture(tmp_path, monkeypatch)
    before = copy.deepcopy(frozen)
    records = scoped.source_contracts(frozen, tmp_path)
    assert frozen == before and len(records) == 1
    assert records[0]['owner'] == 'First' and records[0]['definition_line'] == 2
    assert records[0]['binding_status'] == 'unique_definition_header'
    assert [r['parameter'] for r in records[0]['declarations']] == ['count']
    assert 'other' not in str(records) and 'answer' not in str(records)
    assert not records[0]['target_API_binding_proven']


@pytest.mark.parametrize('change', [{'start_line': None}, {'start_line': 1}, {'owner': 'Second'}, {'start_line': True}])
def test_unknown_header_or_wrong_owner_emits_no_declarations(tmp_path, monkeypatch, change):
    frozen = fixture(tmp_path, monkeypatch)
    frozen['windows'][0].update(change)
    record = scoped.source_contracts(frozen, tmp_path)[0]
    assert record['binding_status'] == 'unknown_definition_scope' and record['declarations'] == []


def test_source_change_rejected_before_parameters(tmp_path, monkeypatch):
    frozen = fixture(tmp_path, monkeypatch)
    (tmp_path / 'core.py').write_bytes(b'changed')
    with pytest.raises(ValueError, match='identity differs'):
        scoped.source_contracts(frozen, tmp_path)


@pytest.mark.parametrize('status', ['supported_boolean_keyword_subobligation', 'conditional_comparative_hypothesis', 'conditional_regression_hypothesis'])
def test_known_bounded_scope_never_enters_repair(status):
    v = verdict()
    v['behavior']['status'] = status
    gate = scoped.action_gate(v)
    assert gate['action'] == 'INDEPENDENT_DEV_GRADE_ONLY' and gate['DEV_candidate_eligible']
    assert not gate['repair_eligible'] and not gate['canary_ready'] and not gate['full_issue_trusted']


def test_unknown_requests_bounded_production_evidence_without_task_rules():
    v = verdict()
    v['qualification'].update({'unknown': ['unexposed_dependency_source_provenance_unknown'],
                              'program_evidence': {'unexposed_dependency_bindings': [{'symbol': 'Api'}, {'symbol': 'unsafe.path'}]}})
    gate = scoped.action_gate(v)
    assert gate['action'] == 'ACQUIRE_EVIDENCE_OR_ABSTAIN'
    assert gate['bounded_source_requests'] == [{'retrieve': 'Api'}]
    assert not gate['DEV_candidate_eligible']


@pytest.mark.parametrize('change', ['rejected', 'invented_full_trust', 'absent_behavior'])
def test_rejected_or_unknown_scope_cannot_select_candidate(change):
    v = verdict()
    if change == 'rejected':
        v['qualification']['rejected'] = ['public_fixture_constraint_changed']
    elif change == 'invented_full_trust':
        v['trusted_reproducer'] = True
    else:
        v['behavior'] = {}
    gate = scoped.action_gate(v)
    assert not gate['DEV_candidate_eligible'] and not gate['repair_eligible']


def test_unknown_hook_keeps_raw_artifact_but_not_terminal_selection(tmp_path, monkeypatch):
    v = verdict()
    v['qualification']['unknown'] = ['missing source']
    candidate, oracle, execution = {'raw': True}, {'locked': True}, {'runs': []}
    monkeypatch.setattr(scoped, '_execute', lambda *args: ({'status': 'base_witness_semantics_unverified', 'controller_verdict': v}, oracle, candidate, execution))
    feedback, locked, selected, actual = scoped.execute_probe({}, {}, tmp_path, 'image', tmp_path / 'turn', {})
    assert feedback['status'] == 'evidence_required_before_selection'
    assert locked is oracle and selected is None and actual is execution and candidate == {'raw': True}
    assert (tmp_path / 'turn/controller-scope-gate.json').is_file()


def test_actual_nested_hooks_restore_without_editing_frozen_owner():
    base = scoped.base
    original = base.source_contracts, base.execute_probe, base.OUT
    compiled = base.base._compiled
    with scoped.configured(), compiled.configured():
        assert base.source_contracts is scoped.source_contracts
        assert compiled.execute_probe is scoped.execute_probe and compiled.base.loop.execute_probe is scoped.execute_probe
        assert compiled.CAP == 50000 and base.OUT == scoped.OUT
    assert (base.source_contracts, base.execute_probe, base.OUT) == original
