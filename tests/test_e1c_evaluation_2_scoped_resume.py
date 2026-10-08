import json

import pytest

from evals import e1c_evaluation_2_scoped_resume as resume


def record(call, status='completed', tokens=100, task='task'):
    return {'run_id': resume.ORIGINAL.name, 'call_id': call, 'status': status, 'total_tokens': tokens, 'task_id': task}


def test_ledger_accounting_counts_completed_call_once_not_two_events():
    assert resume.ledger_usage([record('a', 'started'), record('a'), record('b', tokens=200)]) == {'task': {'calls': 2, 'tokens': 300}}


@pytest.mark.parametrize('change', [{'status': 'started'}, {'total_tokens': 0}, {'total_tokens': True}, {'run_id': 'new-lineage'}])
def test_ambiguous_or_reset_accounting_cannot_continue(change):
    with pytest.raises(ValueError):
        resume.ledger_usage([{**record('a'), **change}])


def prefix(tmp_path):
    original, destination = tmp_path / 'original', tmp_path / 'new'
    folder = original / 'turn-1'
    folder.mkdir(parents=True)
    payload = {'probe': 'same'}
    frozen = {'source': 'same'}
    oracle = {'locked': 'same'}
    for name, value in [('compiler.json', {'raw_contract': payload}), ('input.json', frozen),
                        ('contract.json', {'oracle': oracle}), ('feedback.json', {'status': 'evidence_required_before_selection'}),
                        ('execution.json', {'runs': [{'returncode': 1}]}), ('response.json', {'response_status': 'received', 'raw': '{"probe":"same"}'})]:
        (folder / name).write_text(json.dumps(value), encoding='utf-8')
    return original, destination, payload, frozen, oracle


def test_cached_probe_never_calls_delegate_and_keeps_lock(tmp_path):
    from types import SimpleNamespace
    original, destination, payload, frozen, oracle = prefix(tmp_path)
    calls = []
    loop = SimpleNamespace(execute_probe=lambda *args, **kwargs: calls.append(args))
    with resume.cached_execution(loop, original, destination, 1) as seen:
        feedback, lock, candidate, execution = loop.execute_probe(payload, frozen, tmp_path, 'image', destination / 'turn-1', {}, None)
        assert feedback['status'] == 'evidence_required_before_selection'
        assert lock == oracle and candidate is None and execution['runs'][0]['returncode'] == 1
    assert seen == [1] and not calls and (destination / 'turn-1/prefix-replay.json').is_file()


@pytest.mark.parametrize('part', ['payload', 'source', 'oracle', 'order'])
def test_changed_prefix_hard_stops_not_a_caught_action_error(tmp_path, part):
    from types import SimpleNamespace
    original, destination, payload, frozen, oracle = prefix(tmp_path)
    loop = SimpleNamespace(execute_probe=lambda *args: pytest.fail('old probe execution forbidden'))
    if part == 'payload':
        payload = {'different': True}
    elif part == 'source':
        frozen = {'different': True}
    elif part == 'oracle':
        oracle = {'different': True}
    turn = 2 if part == 'order' else 1
    with resume.cached_execution(loop, original, destination, 2), pytest.raises(RuntimeError):
        loop.execute_probe(payload, frozen, tmp_path, 'image', destination / f'turn-{turn}', {}, oracle)


def test_only_unstarted_probe_reaches_delegate(tmp_path):
    from types import SimpleNamespace
    original, destination, payload, frozen, oracle = prefix(tmp_path)
    marker = object()
    loop = SimpleNamespace(execute_probe=lambda *args, **kwargs: marker)
    with resume.cached_execution(loop, original, destination, 1):
        with pytest.raises(RuntimeError, match='prefix incomplete'):
            loop.execute_probe({}, {}, tmp_path, 'image', destination / 'turn-2', {})
        loop.execute_probe(payload, frozen, tmp_path, 'image', destination / 'turn-1', {}, oracle)
        assert loop.execute_probe({}, {}, tmp_path, 'image', destination / 'turn-2', {}) is marker


def test_cached_response_has_zero_new_usage_and_preserves_exact_raw(tmp_path):
    original, *_ = prefix(tmp_path)
    message = resume.cached_response(original, 1)
    assert message.content == '{"probe":"same"}' and message.usage_metadata['total_tokens'] == 0


def test_nested_resume_hooks_preserve_projection_and_cumulative_budget():
    old_out, old_preflight = resume.parent.OUT, resume.parent.preflight
    with resume.configured() as compiled:
        with compiled.configured():
            assert compiled.base.loop.execute_probe is resume.projection.execute_probe
            assert compiled.preflight is resume.preflight and compiled.CAP == 50000 and compiled.TASK_CAP == 24000
            assert resume.parent.OUT == resume.OUT and resume.OUT != resume.ORIGINAL
    assert (resume.parent.OUT, resume.parent.preflight) == (old_out, old_preflight)
