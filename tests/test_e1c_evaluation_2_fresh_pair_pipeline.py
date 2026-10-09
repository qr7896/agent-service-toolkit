import asyncio
import hashlib
import json
from types import SimpleNamespace

import httpx
import pytest

from evals import e1c_evaluation_2_fresh_pair_pipeline as method


def view():
    return {'issue': 'public requested behavior', 'base_commit': 'a' * 40, 'input_sha256': 'STALE_PARENT_ID',
            'windows': [{'path': 'module.py', 'text': 'x = 1'}, {'path': 'examples/demo.py', 'text': 'not library'}]}


def test_canonical_identity_is_recomputed_after_supplement_and_removes_nonlibrary_views():
    original = view()
    result = method.canonical_input(original)
    assert result['input_sha256'] != 'STALE_PARENT_ID'
    assert result['candidate_paths'] == ['module.py'] and len(result['windows']) == 1
    assert original['input_sha256'] == 'STALE_PARENT_ID' and len(original['windows']) == 2
    changed = view()
    changed['windows'][0]['text'] = 'x = 2'
    assert method.canonical_input(changed)['input_sha256'] != result['input_sha256']


def execution(rc, tail='', hash_='stable'):
    return {'runs': [{'returncode': rc, 'tail': tail, 'log_sha256': hash_} for _ in range(2)]}


def test_operational_pair_gate_keeps_semantic_and_setup_boundaries():
    assert method.paired_gate(execution(0), execution(1, 'AssertionError: expected requested behavior'))
    assert not method.paired_gate(execution(1), execution(1))
    assert not method.paired_gate(execution(0), execution(0))
    assert not method.paired_gate(execution(0), execution(1, 'NameError: unrelated fixture'))
    assert not method.paired_gate(execution(0), {'runs': execution(1)['runs'][:1]})


def test_pair_codec_rejects_constant_or_identical_checks_without_rewriting_source(monkeypatch):
    monkeypatch.setattr(method, 'validate_candidate', lambda src, quote, view, **kw: {
        'source': src, 'probe_sha256': hashlib.sha256(src.encode()).hexdigest()})
    value = {'normal_source': 'assert supported()', 'target_source': 'assert requested()', 'issue_quote': 'public'}
    assert set(method.validate_pair(json.dumps(value), {}, None)) == {'normal', 'target'}
    with pytest.raises(ValueError, match='constant-only'):
        method.validate_pair(json.dumps({**value, 'target_source': 'assert 1 == 2'}), {}, None)
    with pytest.raises(ValueError, match='must differ'):
        method.validate_pair(json.dumps({**value, 'target_source': value['normal_source']}), {}, None)


def test_missing_whole_producer_seal_stops_before_private_scoring(tmp_path, monkeypatch):
    monkeypatch.setattr(method, 'OUT', tmp_path)
    monkeypatch.setattr(method, 'grade_one', lambda *args: pytest.fail('must not open scorer'))
    with pytest.raises(FileNotFoundError):
        method.grade()


def test_actual_generator_runs_paired_public_feedback_and_seals_two_tasks_before_score(tmp_path, monkeypatch):
    from core.settings import settings

    monkeypatch.setattr(method, 'OUT', tmp_path)
    inputs = [{'instance_id': name, 'image_id': 'image', 'input': method.canonical_input(view()),
               'missing_optional_import': None} for name in ('library-a', 'library-b')]
    frozen = {'tasks': [{'instance_id': r['instance_id'], 'initial_prompt_sha256': hashlib.sha256(
        method._prompt_text(method.messages(r['input'], 'probe')).encode()).hexdigest()} for r in inputs]}
    monkeypatch.setattr(method, 'preflight', lambda: frozen)
    (tmp_path / 'freeze.json').write_text(json.dumps(frozen), encoding='utf-8')
    monkeypatch.setattr(method, 'inputs', lambda: inputs)
    monkeypatch.setattr(method, 'require_engine', lambda *args: True)
    monkeypatch.setattr(settings, 'DEEPSEEK_API_KEY', 'fixture-key')

    class FakeModel:
        def __init__(self, **kwargs):
            assert kwargs['model'] == 'deepseek-flash' and kwargs['max_retries'] == 0

        def bind(self, **kwargs):
            assert kwargs['extra_body'] == {'thinking': {'type': 'enabled'}}
            assert kwargs['reasoning_effort'] == 'high'
            return self

    monkeypatch.setattr(method, 'FreshFlash', FakeModel)
    calls = []

    async def invoke(model, msgs, config, *, role):
        calls.append((msgs, config, role))
        conf = config['configurable']
        with (tmp_path / 'provider_calls.jsonl').open('a', encoding='utf-8') as handle:
            handle.write(json.dumps({'call_id': str(len(calls)), 'run_id': method.RUN_ID,
                'status': 'completed', 'task_id': conf['provider_task_id'], 'total_tokens': 100}) + '\n')
        value = {'normal_source': 'assert normal()', 'target_source': 'assert target()', 'issue_quote': 'public'} if role == 'fresh_probe' else {'edits': []}
        return SimpleNamespace(content=json.dumps(value), usage_metadata={'total_tokens': 100},
                               response_metadata={'finish_reason': 'stop'})

    monkeypatch.setattr(method, 'budgeted_ainvoke', invoke)
    monkeypatch.setattr(method, 'validate_pair', lambda raw, *args: {phase: {
        'source': phase, 'issue_quote': 'public', 'probe_sha256': phase} for phase in ('normal', 'target')})
    executions = []

    def run_probe(candidate, row, root, candidate_patch=None):
        executions.append((candidate['source'], root.name, candidate_patch is not None))
        return execution(1 if candidate['source'] == 'target' and candidate_patch is None else 0, 'own public failure')

    monkeypatch.setattr(method, 'run_probe', run_probe)
    monkeypatch.setattr(method.edits, 'compile_patch', lambda *args: 'production patch')
    results = asyncio.run(method.generate())
    assert len(calls) == 4 and all(r['operational_pair_valid'] and r['own_post_patch_pass'] for r in results)
    assert len(executions) == 8 and all(r['full_issue_trusted'] is False for r in results)
    assert [c[1]['configurable']['provider_total_token_ceiling'] for c in calls] == [50_000, 50_000, 100_000, 100_000]
    assert all(c[1]['configurable']['provider_max_calls_per_task'] == 2 for c in calls)
    assert 'own public failure' in method._prompt_text(calls[1][0])
    assert not list(tmp_path.rglob('official*'))
    seal = json.loads((tmp_path / 'generation-seal.json').read_bytes())
    assert seal['official_scoring_not_started'] is True
    assert all(method._sha(tmp_path / p) == h for p, h in seal['files'].items())


@pytest.mark.parametrize('files,error', [({'../outside': 'x'}, 'unsafe'), ({}, 'incomplete')])
def test_bad_producer_seal_never_opens_independent_grader(tmp_path, monkeypatch, files, error):
    monkeypatch.setattr(method, 'OUT', tmp_path)
    method._save(tmp_path / 'freeze.json', {'tasks': [{'instance_id': 'library'}]})
    method._save(tmp_path / 'generation-seal.json', {'files': files, 'official_scoring_not_started': True})
    monkeypatch.setattr(method, 'grade_one', lambda *a: pytest.fail('private grading must remain closed'))
    with pytest.raises(ValueError, match=error):
        method.grade()


@pytest.mark.parametrize('target,regression,identity,valid,rc,resolved', [
    (True, True, True, True, 0, True), (False, True, True, True, 0, False),
    (True, False, True, True, 0, False), (True, True, False, True, 0, False),
    (True, True, True, False, 0, False), (True, True, True, True, 91, False)])
def test_official_score_requires_targets_regressions_identity_and_valid_log(
        tmp_path, monkeypatch, target, regression, identity, valid, rc, resolved):
    from evals import e1c_evaluation_2_admission as scorer

    monkeypatch.setattr(scorer, 'OUT', tmp_path / 'grader')
    grader, root = scorer.OUT / 'library', tmp_path / 'candidate'
    root.mkdir()
    method._save(root / 'generation.json', {'patch_written': True})
    (root / 'candidate.patch').write_text('production fixture', encoding='utf-8')
    method._save(grader / 'tests.json', {'FAIL_TO_PASS': ['target'], 'PASS_TO_PASS': ['regression']})
    method._save(grader / 'task.yaml', {'log_parser': 'fixture'})  # JSON is valid YAML.
    for name in set(scorer.FILES) - {'tests.json', 'task.yaml'}:
        (grader / name).write_text('fixture only', encoding='utf-8')
    method._save(grader / 'materialization.json', {'instance_id': 'library',
        'sha256': {name: method._sha(grader / name) for name in scorer.FILES}})
    monkeypatch.setattr(scorer, '_task', lambda _: ({'base_commit': 'base', 'image': 'fixture', 'repo': 'fixture'}, None))
    monkeypatch.setattr(scorer, '_official_grader', lambda: (
        lambda *a: ({'target': target, 'regression': regression}, valid),
        lambda c, statuses: statuses[c], lambda c, statuses: statuses[c], None, lambda **kw: kw))

    def run(command, **kw):
        assert command[:2] == ['docker', 'run'] and command[command.index('--network') + 1] == 'none'
        assert '--pull=never' in command and 'fixture-image' in command
        assert all('readonly' in command[n + 1] for n, part in enumerate(command) if part == '--mount')
        kw['stdout'].write(b'E1C2_SOURCE_IDENTITY:PASS\n' if identity else b'identity failed\n')
        return SimpleNamespace(returncode=rc)

    monkeypatch.setattr(method.subprocess, 'run', run)
    result = method.grade_one({'instance_id': 'library', 'input': {'base_commit': 'base'}, 'image_id': 'fixture-image'}, root)
    assert result['resolved'] is resolved and result['f2p_pass'] == int(target)
    assert result['p2p_maintained'] == int(regression) and result['official_scoring_attempted']


def test_elastic_output_cannot_spend_below_registered_reasoning_floor(tmp_path, monkeypatch):
    monkeypatch.setattr(method, 'OUT', tmp_path)
    monkeypatch.setattr(method, 'spent', lambda _: 49_000)
    monkeypatch.setattr(method, 'budgeted_ainvoke', lambda *a, **k: pytest.fail('budget must block HTTP'))
    row = {'instance_id': 'old-dev', 'input': method.canonical_input(view())}
    with pytest.raises(method.ProviderBudgetExceeded, match='>=16k'):
        asyncio.run(method.call(None, row, 'repair', {}, tmp_path / 'call', 100_000))
    assert not (tmp_path / 'call').exists()


def test_fresh_sdk_actual_http_wire_reasoning_and_budget_are_checked_offline(tmp_path, monkeypatch):
    monkeypatch.setattr(method, 'OUT', tmp_path)
    seen = []

    def handler(request):
        body = json.loads(request.content)
        assert body['model'] == 'deepseek-flash' and body['thinking'] == {'type': 'enabled'}
        assert body['reasoning_effort'] == 'high' and body['max_tokens'] == 20_000
        assert request.extensions['timeout']['read'] == 300
        seen.append(body)
        return httpx.Response(200, json={'id': 'fixture', 'created': 1, 'object': 'chat.completion', 'model': 'deepseek-flash',
            'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '{"normal_source":"own","target_source":"other","issue_quote":"public"}',
                                              'reasoning_content': 'fixture-private-reasoning'}, 'finish_reason': 'stop'}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 20, 'total_tokens': 30,
                      'completion_tokens_details': {'reasoning_tokens': 15}}})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as client:
            model = method.FreshFlash(model='deepseek-flash', openai_api_key='fixture-key',
                openai_api_base='https://example.invalid', max_retries=0, http_async_client=client).bind(
                    response_format={'type': 'json_object'}, extra_body={'thinking': {'type': 'enabled'}}, reasoning_effort='high')
            await method.call(model, {'instance_id': 'fixture', 'input': method.canonical_input(view())},
                              'probe', None, tmp_path / 'call', 50_000)

    asyncio.run(run())
    record = json.loads((tmp_path / 'call/response.json').read_bytes())
    assert len(seen) == 1 and record['wire_max_tokens'] == 20_000
    assert record['reasoning_tokens_reported'] == 15 and record['usage']['total_tokens'] == 30
    assert 'fixture-private-reasoning' not in json.dumps(record)
