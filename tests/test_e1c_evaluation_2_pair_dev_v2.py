import asyncio
import hashlib
import json
from types import SimpleNamespace

import pytest

from evals import e1c_evaluation_2_pair_dev_v2 as method


@pytest.mark.parametrize('source', [
    'import library as lib\nlib.available = False\nassert check()',
    'from library import utils\nutils.available = False\nassert check()',
    'import library as lib\nx = lib\ny = x\ny.available = False\nassert check()',
    'import library as lib\nsetattr(lib, "available", False)\nassert check()',
    'import library as lib\nlib = fake()\nassert check()',
])
def test_namespace_condition_manufacturing_rejected_without_rewriting_probe(monkeypatch, source):
    monkeypatch.setattr(method.shared, 'validate_pair', lambda *a: {'normal': {'source': source}})
    with pytest.raises(ValueError, match='imported'):
        method.validate_pair('', {}, None)


def test_constructed_object_parameter_change_and_readonly_alias_are_allowed(monkeypatch):
    source = 'import library as lib\nalias = lib\nmodel = alias.Model()\nmodel.n_estimators = 4\nassert model.run()'
    monkeypatch.setattr(method.shared, 'validate_pair', lambda *a: {'target': {'source': source}})
    assert method.validate_pair('', {}, None)['target']['source'] == source


def test_lexical_window_partial_last_line_uses_its_original_cap(monkeypatch):
    blob = ('x' * 2300).encode()
    monkeypatch.setattr(method.shared.edits.source.method, 'checked_source', lambda *a: blob)
    monkeypatch.setattr(method.shared.edits.source.method.qualified, 'git_blob', lambda *a: blob)
    window = {'path': 'module.py', 'start_line': 1, 'end_line': 1, 'origin': 'issue_lexical', 'text': 'x' * 2200}
    method.validate_source({'base_commit': 'base', 'windows': [window]}, None)
    with pytest.raises(ValueError, match='exact base slice'):
        method.validate_source({'base_commit': 'base', 'windows': [{**window, 'text': 'changed'}]}, None)


def test_prepare_retains_12_rows_and_selects_next_repo_representatives_without_outcome_ranking(tmp_path, monkeypatch):
    for name, path in {'ROOT': tmp_path, 'PREP': tmp_path / 'prepared', 'SOURCE': tmp_path / 'source',
        'ISSUES': tmp_path / 'issues', 'GRADER': tmp_path / 'grader', 'IDENTITY': tmp_path / 'identity.json',
        'METADATA': tmp_path / 'metadata.json', 'TREE': tmp_path / 'tree.json', 'PROTOCOL': tmp_path / 'protocol.md'}.items():
        monkeypatch.setattr(method, name, path)
    monkeypatch.setattr(method.shared, 'OUT', tmp_path / 'paid-v1')
    for name in ('evals/e1c_evaluation_2_pair_dev_v2.py', 'evals/e1c_evaluation_2_issue_input.py', 'protocol.md'):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('fixture', encoding='utf-8')
    tasks = [{'instance_id': f'task-{n}', 'repo': f'repo-{n // 3}', 'base_commit': 'base'} for n in range(12)]
    method._save(method.IDENTITY, {'role': 'development_only_never_independent_canary_or_fresh30',
        'source_revision': 'revision', 'tasks': tasks})
    method._save(method.METADATA, {'identity_sha256': method._sha(method.IDENTITY), 'source_revision': 'revision', 'tasks': tasks})
    raw = b'public behavior'
    blob = hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()
    method._save(method.TREE, {'source_revision': 'revision', 'sha': {
        f"tasks/{t['instance_id']}/problem_statement.md": blob for t in tasks}})
    method._save(method.shared.OUT / 'freeze.json', {'tasks': [tasks[3], tasks[6]]})
    for task in tasks[3:]:
        iid = task['instance_id']
        (method.SOURCE / iid).mkdir(parents=True)
        (method.ISSUES / iid).mkdir(parents=True)
        (method.ISSUES / iid / 'problem_statement.md').write_bytes(raw)
        for phase in ('base', 'gold'):
            method._save(method.GRADER / iid / (phase + '.json'), {'phase_pass': True})
    monkeypatch.setattr(method, 'freeze_input', lambda issue, *a, **k: {'issue': issue, 'base_commit': 'base',
        'windows': [{'path': 'module.py', 'text': 'old = 1', 'origin': 'fixture'}]})
    monkeypatch.setattr(method, 'validate_source', lambda *a: None)
    monkeypatch.setattr(method.shared.globals_method, 'loaded_globals', lambda *a: [])
    monkeypatch.setattr(method.shared, 'verified_local_image', lambda _: 'image')
    result = method.prepare()
    assert len(result['rows']) == 12 and sum(r['status'] == 'ready' for r in result['rows']) == 9
    assert [r['instance_id'] for r in method.selected_rows()] == ['task-4', 'task-7']
    with pytest.raises(FileExistsError, match='no retry'):
        method.prepare()
    (method.GRADER / 'task-4/base.json').write_text('{}', encoding='utf-8')
    with pytest.raises(ValueError, match='prepared source identity'):
        method.selected_rows()


def test_actual_v2_generation_call_decodes_before_compile_and_seals_before_score(tmp_path, monkeypatch):
    from core.settings import settings

    monkeypatch.setattr(method, 'OUT', tmp_path)
    view = method.shared.canonical_input({'issue': 'public behavior', 'base_commit': 'base',
        'windows': [{'path': 'module.py', 'text': 'old = 1', 'origin': 'fixture'}]})
    rows = [{'instance_id': iid, 'image_id': 'image', 'input': view, 'missing_optional_import': None} for iid in ('a', 'b')]
    frozen = {'tasks': [{'initial_prompt_sha256': hashlib.sha256(method._prompt_text(method.messages(view, 'probe')).encode()).hexdigest()} for _ in rows]}
    method._save(tmp_path / 'freeze.json', frozen)
    monkeypatch.setattr(method, 'preflight', lambda: frozen)
    monkeypatch.setattr(method, 'selected_rows', lambda: rows)
    monkeypatch.setattr(settings, 'DEEPSEEK_API_KEY', 'fixture-key')
    monkeypatch.setattr(method.shared, 'require_engine', lambda *a: True)

    class Model:
        def __init__(self, **kw):
            assert kw['model'] == 'deepseek-flash' and kw['max_retries'] == 0

        def bind(self, **kw):
            assert kw['reasoning_effort'] == 'high'
            return self

    monkeypatch.setattr(method.shared, 'FreshFlash', Model)
    calls, compiled, scored = [], [], []
    edit = {'path': 'module.py', 'old': 'old = 1', 'new': 'old = 2'}

    async def invoke(model, msgs, config, *, role):
        calls.append((role, config['configurable']))
        conf = config['configurable']
        with (tmp_path / 'provider_calls.jsonl').open('a', encoding='utf-8') as handle:
            handle.write(json.dumps({'run_id': method.RUN_ID, 'call_id': str(len(calls)), 'task_id': conf['provider_task_id'],
                'status': 'completed', 'total_tokens': 100}) + '\n')
        value = {'normal_source': 'normal', 'target_source': 'target', 'issue_quote': 'public'} if role.endswith('probe') else {'type': 'json_object', 'edits': [edit]}
        return SimpleNamespace(content=json.dumps(value), usage_metadata={'total_tokens': 100}, response_metadata={'finish_reason': 'stop'})

    monkeypatch.setattr(method, 'budgeted_ainvoke', invoke)
    monkeypatch.setattr(method, 'validate_pair', lambda *a: {phase: {'source': phase, 'issue_quote': 'public'} for phase in ('normal', 'target')})
    monkeypatch.setattr(method.shared, 'run_probe', lambda candidate, row, root, patch=None: {
        'runs': [{'returncode': int(candidate['source'] == 'target' and patch is None), 'log_sha256': 'stable', 'tail': 'own behavior'}] * 2})

    def compile_patch(raw, *a):
        assert json.loads(raw) == {'edits': [edit]}
        assert len(calls) > len(compiled)
        compiled.append(raw)
        return 'fixture patch'

    monkeypatch.setattr(method.shared.edits, 'compile_patch', compile_patch)

    def grade(row, root):
        assert len(calls) == 4
        seal = method.shared.edits._read(tmp_path / 'generation-seal.json')
        assert all(method._sha(tmp_path / p) == h for p, h in seal['files'].items())
        assert method.shared.edits._read(root / 'generation.json')['own_post_patch_pass']
        scored.append(row['instance_id'])
        return {'instance_id': row['instance_id'], 'resolved': True}

    monkeypatch.setattr(method.shared, 'grade_one', grade)
    result = asyncio.run(method.run())
    assert len(compiled) == 2 and scored == ['a', 'b'] and result['fixed_tasks'] == 2
    assert [conf['provider_total_token_ceiling'] for _, conf in calls] == [50_000,50_000,100_000,100_000]
    assert all(method.shared.edits._read(tmp_path / r['instance_id'] / 'repair-call/canonical.json')['known_envelope_removed'] for r in rows)
    assert result['full_issue_trusted'] is False and result['official_feedback_sent_to_actor'] is False
    with pytest.raises(FileExistsError, match='no retry'):
        asyncio.run(method.run())


def test_budget_floor_blocks_v2_actual_call_before_sdk(tmp_path, monkeypatch):
    monkeypatch.setattr(method, 'OUT', tmp_path)
    monkeypatch.setattr(method, '_events', lambda *a: [{'call_id': 'one', 'status': 'completed', 'task_id': 'a', 'total_tokens': 49_000}])
    monkeypatch.setattr(method, 'budgeted_ainvoke', lambda *a: pytest.fail('must not call provider'))
    with pytest.raises(method.ProviderBudgetExceeded):
        asyncio.run(method.call(None, {'instance_id': 'a', 'input': {'issue': 'public', 'base_commit': 'base', 'windows': []}},
            'probe', None, tmp_path / 'request', 50_000))
    assert not (tmp_path / 'request').exists()
