import copy
import hashlib
import json

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from evals import e1c_evaluation_2_acquisition_context as adapter
from evals.e1c_blind_boundary import BlindBoundaryViolation


def fixture(tmp_path, monkeypatch):
    raw = b'class Api:\n    def __init__(self):\n        pass\n'
    (tmp_path / 'core.py').write_bytes(raw)
    monkeypatch.setattr(adapter.qualified, 'git_blob', lambda *args: raw)
    frozen = {'base_commit': 'b' * 40, 'issue': 'public issue', 'windows': []}
    feedback = {'status': 'evidence_required_before_selection', 'controller_verdict': {
        'status': 'unknown_or_rejected_dependency_evidence', 'trusted_reproducer': False,
        'program': {'unknown': ['unexposed_dependency_source_provenance_unknown'], 'rejected': [],
                    'unexposed_dependency_bindings': [{'module': 'core', 'symbol': 'Api', 'path': 'core.py'}]}}}
    return frozen, adapter.routing.route(feedback)


def test_real_ast_acquisition_next_message_and_next_execution_do_not_mutate_input(tmp_path, monkeypatch):
    frozen, feedback = fixture(tmp_path, monkeypatch)
    before = copy.deepcopy(frozen)
    received = []

    def delegate(payload, visible, *args):
        received.append(copy.deepcopy(visible))
        return feedback, {'locked': True}, None, None

    monkeypatch.setattr(adapter, '_execute', delegate)
    monkeypatch.setattr(adapter, 'public_body', lambda visible, feedback: {'windows': visible['windows'], 'last_feedback': feedback})
    with adapter.configured():
        result = adapter.execute_probe({}, frozen, tmp_path, 'image', tmp_path / 'turn-1', {})
        assert result[2] is None and result[0]['new_evidence_requires_next_probe']
        assert result[0]['automatic_source_acquisition'][0]['source_sha256'] == hashlib.sha256((tmp_path / 'core.py').read_bytes()).hexdigest()
        body = json.loads(adapter.messages(frozen, result[0], {'probe': 'previous'})[1].content)
        assert body['windows'][0]['path'] == 'core.py' and 'previous_probe' not in body
        adapter.execute_probe({}, frozen, tmp_path, 'image', tmp_path / 'turn-2', {})
    assert not received[0]['windows'] and received[1]['windows'][0]['path'] == 'core.py'
    assert frozen == before and adapter._views.get() is None


def test_changed_canonical_dependency_is_hard_failure(tmp_path, monkeypatch):
    frozen, feedback = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(adapter.qualified, 'git_blob', lambda *args: b'other source')
    with adapter.configured(), pytest.raises(RuntimeError, match='canonical base'):
        adapter.acquire(frozen, tmp_path, feedback, tmp_path / 'turn')


def test_duplicate_requests_and_cap_and_issue_scope(tmp_path, monkeypatch):
    frozen, feedback = fixture(tmp_path, monkeypatch)
    with adapter.configured():
        assert adapter.acquire(frozen, tmp_path, feedback, tmp_path / 't1')
        assert adapter.acquire(frozen, tmp_path, feedback, tmp_path / 't2') == []
        state = adapter._views.get()[adapter.view_key(frozen)]
        state['seen'].append(('other', 'Symbol'))
        extra = copy.deepcopy(feedback)
        extra['controller_verdict']['program']['unexposed_dependency_bindings'][0]['symbol'] = 'Missing'
        assert adapter.acquire(frozen, tmp_path, extra, tmp_path / 't3') == []
        assert adapter.effective({**frozen, 'issue': 'different public issue'})['windows'] == []


def test_rejected_feedback_does_not_acquire(tmp_path, monkeypatch):
    frozen, feedback = fixture(tmp_path, monkeypatch)
    feedback['scope_gate']['action'] = 'REJECT'
    with adapter.configured():
        assert adapter.acquire(frozen, tmp_path, feedback, tmp_path / 'turn') == []


def test_compaction_preserves_unknown_rejection_scope_and_behavior_reasons():
    feedback = {'status': 'evidence_required_before_selection', 'scope_gate': {'rejected': ['rejected'], 'repair_eligible': False},
                'controller_verdict': {'status': 'controller_qualification_recorded', 'trusted_reproducer': False,
                    'source_projection': [{'duplicate_proof': 'x' * 10000}],
                    'qualification': {'schema': 'e1c2-bounded-qualification-v2', 'Gold_used': False, 'unknown': ['missing'], 'rejected': ['rejected'], 'status': 'unknown'},
                    'behavior': {'schema': 'e1c2-bounded-behavior-gate-v1', 'Gold_used': False, 'status': 'unknown', 'reasons': ['scope missing'], 'trusted_reproducer': False}}}
    result = adapter.compact_feedback(feedback)
    assert len(str(result)) < len(str(feedback))
    assert result['scope_gate'] == feedback['scope_gate']
    assert result['controller_verdict']['qualification']['unknown'] == ['missing']
    assert result['controller_verdict']['qualification']['rejected'] == ['rejected']
    assert result['controller_verdict']['behavior']['reasons'] == ['scope missing']


def test_compaction_does_not_hide_real_scoring_marker():
    with pytest.raises(BlindBoundaryViolation):
        adapter.compact_feedback({'status': 'gold.patch expected answer'})


def test_action_history_is_not_falsely_claimed_as_retrieval():
    base = [SystemMessage(content=adapter.POLICY), HumanMessage(content='{}')]
    result = adapter.conversation(base, 3, '{"probe":{}}', {'status': 'source required'})
    assert 'Previous action kind: probe' in result[-1].content
    assert 'retrieval has already completed' not in result[-1].content
    assert len(result) == 4 and result[-2].content == '{"probe":{}}'


def test_nested_hooks_preserve_actual_adapter_and_restore_owners():
    from evals import e1c_evaluation_2_scoped_dev_trial as trial
    before = adapter.scope.execute_probe, adapter.qualified.messages
    with adapter.configured(), trial.configured(), trial.method.base.base._compiled.configured():
        compiled = trial.method.base.base._compiled
        assert compiled.base.loop.execute_probe is adapter.execute_probe
        assert compiled.base.loop.messages is adapter.messages and compiled.conversation is adapter.conversation
    assert (adapter.scope.execute_probe, adapter.qualified.messages) == before


def test_resume_nested_projection_does_not_replace_acquisition_hook():
    from evals import e1c_evaluation_2_scoped_resume as previous
    with adapter.configured(), previous.configured() as compiled, compiled.configured():
        assert compiled.base.loop.execute_probe is adapter.execute_probe
        assert compiled.base.loop.messages is adapter.messages and compiled.conversation is adapter.conversation
