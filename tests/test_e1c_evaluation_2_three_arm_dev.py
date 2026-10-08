import hashlib
import json
import subprocess

import pytest

from evals import e1c_evaluation_2_base_tests as gateway
from evals import e1c_evaluation_2_three_arm_dev as pilot


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args]).decode().strip()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'user.name', 'fixture')
    git(tmp_path, 'config', 'user.email', 'fixture@example.invalid')
    git(tmp_path, 'config', 'core.autocrlf', 'false')
    (tmp_path / 'tests').mkdir()
    (tmp_path / 'tests/test_old.py').write_text('def test_DateTime():\n    assert DateTime() == 1\n', encoding='utf-8')
    (tmp_path / 'module.py').write_text('x = 1\n', encoding='utf-8')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-qm', 'base')
    base = git(tmp_path, 'rev-parse', 'HEAD')
    return tmp_path, base


def test_gateway_reads_base_not_modified_checkout_or_future_commit(repo):
    root, base = repo
    (root / 'tests/test_old.py').write_text('FUTURE_SCORING_SECRET\n', encoding='utf-8')
    (root / 'tests/test_new.py').write_text('def test_DateTime(): FUTURE_TEST_ANSWER\n', encoding='utf-8')
    git(root, 'add', '.')
    git(root, 'commit', '-qm', 'future grading change')
    result = gateway.retrieve(root, base, ['DateTime'])
    text = json.dumps(result)
    assert 'assert DateTime() == 1' in text
    assert 'FUTURE_SCORING_SECRET' not in text and 'FUTURE_TEST_ANSWER' not in text
    assert result['scanned_files'] == 1 and result['checkout_test_content_read'] is False
    blob, oid = gateway.base_blob(root, base, 'tests/test_old.py')
    assert result['windows'][0]['git_blob_oid'] == oid
    assert result['windows'][0]['source_sha256'] == hashlib.sha256(blob).hexdigest()
    with pytest.raises(ValueError, match='absent from base'):
        gateway.base_blob(root, base, 'tests/test_new.py')


@pytest.mark.parametrize('path', [None, '../tests/x.py', '/tests/x.py', 'C:/tests/x.py',
                                 'tests\\x.py', 'tests/./x.py', 'tests//x.py',
                                 '.codex/tests/x.py', 'grader-only/tests/x.py', 'tests/x\ny.py'])
def test_gateway_rejects_unsafe_or_protected_paths(path):
    with pytest.raises(ValueError):
        gateway.safe_test_path(path)


@pytest.mark.parametrize('base', ['HEAD', 'main', 'abc', 'a' * 39 + ':'])
def test_gateway_requires_exact_base_not_a_ref(repo, base):
    with pytest.raises(ValueError, match='exact base'):
        gateway.retrieve(repo[0], base, ['DateTime'])


def test_regular_production_and_symlink_not_test_readable(repo):
    root, base = repo
    with pytest.raises(ValueError, match='only base Python test'):
        gateway.base_blob(root, base, 'module.py')
    oid = git(root, 'hash-object', 'module.py')
    git(root, 'update-index', '--add', '--cacheinfo', '120000,' + oid + ',tests/test_link.py')
    git(root, 'commit', '-qm', 'symlink fixture')
    linked = git(root, 'rev-parse', 'HEAD')
    with pytest.raises(ValueError, match='regular base blobs'):
        gateway.base_blob(root, linked, 'tests/test_link.py')


def body():
    return {'issue': 'ordinary defect', 'base_commit': 'a' * 40,
            'windows': [{'path': 'module.py', 'text': 'x = 1\n'}]}


def test_arms_share_production_separate_test_lane_and_do_not_upgrade_trust():
    context = {'windows': [{'text': 'BASE_ASSERTION'}]}
    witness = {'own_target_probe': 'OWN_PROBE', 'full_issue_trusted': False, 'remaining_unknown': ['intent_unknown']}
    cells = pilot.arm_payloads(body(), context, witness)
    assert 'conditional_evidence' not in cells['standard']
    assert cells['standard']['base_tests'] == cells['standard_evidence']['base_tests']
    assert 'base_tests' not in cells['strict_evidence']
    assert cells['standard_evidence']['conditional_evidence'] == cells['strict_evidence']['conditional_evidence']
    strict_message = pilot._prompt_text(pilot.messages(cells['strict_evidence']))
    assert 'BASE_ASSERTION' not in strict_message and 'OWN_PROBE' in strict_message
    assert cells['standard_evidence']['conditional_evidence']['full_issue_trusted'] is False
    assert len({json.dumps(c['production_windows']) for c in cells.values()}) == 1


def test_compile_production_patch_does_not_modify_workspace(repo):
    root, base = repo
    b = {**body(), 'base_commit': base, 'allowed_production_paths': ['module.py'], 'production_windows': body()['windows']}
    raw = json.dumps({'edits': [{'path': 'module.py', 'old': 'x = 1', 'new': 'x = 2'}]})
    patch = pilot.compile_patch(raw, b, root)
    assert '-x = 1' in patch and '+x = 2' in patch
    assert (root / 'module.py').read_text() == 'x = 1\n'
    assert git(root, 'status', '--porcelain') == ''


def test_patch_rejects_unexposed_source_test_edits_and_invalid_python(repo):
    root, base = repo
    b = {**body(), 'base_commit': base, 'allowed_production_paths': ['module.py'], 'production_windows': body()['windows']}
    for name, old, new, error in [('tests/test_old.py', 'a', 'b', PermissionError),
                                 ('module.py', 'not exposed', 'b', ValueError),
                                 ('module.py', 'x = 1', 'x = (', SyntaxError)]:
        with pytest.raises(error):
            pilot.compile_patch(json.dumps({'edits': [{'path': name, 'old': old, 'new': new}]}), b, root)


def seal(root):
    for name in ('freeze.json', 'started.json', 'provider_calls.jsonl'):
        (root / name).write_text('{}', encoding='utf-8')
    for arm in pilot.ARMS:
        (root / arm).mkdir()
        (root / arm / 'input.json').write_text('{}', encoding='utf-8')
        (root / arm / 'response.json').write_text('{}', encoding='utf-8')
        (root / arm / 'generation.json').write_text('{"status":"candidate_rejected"}', encoding='utf-8')
    files = {p.relative_to(root).as_posix(): pilot._sha(p) for p in root.rglob('*') if p.is_file()}
    (root / 'generation-seal.json').write_text(json.dumps({'files': files, 'official_scoring_not_started': True}), encoding='utf-8')


def test_seal_requires_all_three_cells_and_rejects_tampering(tmp_path):
    seal(tmp_path)
    pilot.verify_seal(tmp_path)
    (tmp_path / 'standard/response.json').write_text('changed', encoding='utf-8')
    with pytest.raises(ValueError, match='seal differs'):
        pilot.verify_seal(tmp_path)


def test_scoring_cannot_start_without_generation_seal(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, 'OUT', tmp_path)
    with pytest.raises(FileNotFoundError):
        pilot.grade()
    assert list(tmp_path.iterdir()) == []


def test_repeat_generation_stops_before_engine_or_provider(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, 'OUT', tmp_path)
    monkeypatch.setattr(pilot, 'preflight', lambda: {})
    (tmp_path / 'freeze.json').write_text('{}', encoding='utf-8')
    (tmp_path / 'started.json').write_text('{}', encoding='utf-8')
    monkeypatch.setattr(pilot, 'require_engine', lambda *a: pytest.fail('must not call engine'))
    import asyncio
    with pytest.raises(FileExistsError, match='already started'):
        asyncio.run(pilot.generate())


def test_real_generation_hook_three_calls_equal_caps_seal_and_no_scorer_reads(tmp_path, monkeypatch):
    import asyncio
    from types import SimpleNamespace

    from core.settings import settings

    monkeypatch.setattr(pilot, 'OUT', tmp_path)
    frozen = {'instance_id': 'old-dev', 'image_id': 'sha256:fixture'}
    monkeypatch.setattr(pilot, 'preflight', lambda: frozen)
    (tmp_path / 'freeze.json').write_text(json.dumps(frozen), encoding='utf-8')
    cells = pilot.arm_payloads(body(), {'windows': [{'text': 'BASE_ASSERTION'}]}, {'full_issue_trusted': False})
    frozen['cells'] = [{'prompt_sha256': hashlib.sha256(pilot._prompt_text(pilot.messages(cells[arm])).encode()).hexdigest()}
                       for arm in pilot.ARMS]
    (tmp_path / 'freeze.json').write_text(json.dumps(frozen), encoding='utf-8')
    monkeypatch.setattr(pilot, 'inputs', lambda: (None, cells, {}))
    monkeypatch.setattr(pilot, 'require_engine', lambda *a: True)
    monkeypatch.setattr(settings, 'DEEPSEEK_API_KEY', 'fixture-not-a-real-secret')

    class FakeModel:
        def __init__(self, **kwargs):
            assert kwargs['model'] == 'deepseek-flash' and kwargs['max_retries'] == 0

        def bind(self, **kwargs):
            assert kwargs == {'response_format': {'type': 'json_object'}}
            return self

    monkeypatch.setattr(pilot, 'RawJsonFlash', FakeModel)
    calls = []

    async def fake_invoke(model, messages, config, *, role):
        conf = config['configurable']
        calls.append((messages, conf, role))
        with (tmp_path / 'provider_calls.jsonl').open('a') as ledger:
            ledger.write(json.dumps({'status': 'completed', 'task_id': conf['provider_task_id'], 'total_tokens': 100}) + '\n')
        return SimpleNamespace(content='{"edits":[]}', usage_metadata={'total_tokens': 100},
                               response_metadata={'finish_reason': 'stop', 'model_name': 'deepseek-flash'})

    monkeypatch.setattr(pilot, 'budgeted_ainvoke', fake_invoke)
    asyncio.run(pilot.generate())
    assert len(calls) == 3
    assert [c[1]['provider_total_token_ceiling'] for c in calls] == [16_000, 32_000, 48_000]
    assert {c[1]['provider_task_token_ceiling'] for c in calls} == {16_000}
    assert {c[1]['provider_max_calls_per_task'] for c in calls} == {1}
    assert 'BASE_ASSERTION' not in pilot._prompt_text(calls[2][0])
    assert not list(tmp_path.rglob('official*'))
    pilot.verify_seal(tmp_path)


@pytest.mark.parametrize('rc,identity,valid,p2p_ok,resolved', [
    (0, True, True, True, True), (1, True, True, True, False),
    (0, False, True, True, False), (0, True, False, True, False),
    (0, True, True, False, False)])
def test_official_grade_real_hook_requires_identity_exit_f2p_p2p_and_no_model_feedback(
        tmp_path, monkeypatch, rc, identity, valid, p2p_ok, resolved):
    from types import SimpleNamespace

    from evals import e1c_evaluation_2_admission as scorer

    root = tmp_path / 'run'
    root.mkdir()
    monkeypatch.setattr(pilot, 'OUT', root)
    frozen = {'instance_id': 'old-dev', 'image_id': 'sha256:fixture', 'base_commit': 'a' * 40}
    seal(root)
    (root / 'freeze.json').write_text(json.dumps(frozen), encoding='utf-8')
    for arm in pilot.ARMS:
        (root / arm / 'generation.json').write_text('{"status":"candidate"}', encoding='utf-8')
        (root / arm / 'candidate.patch').write_text('production diff', encoding='utf-8')
    files = {p.relative_to(root).as_posix(): pilot._sha(p) for p in root.rglob('*')
             if p.is_file() and p.name != 'generation-seal.json'}
    (root / 'generation-seal.json').write_text(json.dumps({'files': files, 'official_scoring_not_started': True}), encoding='utf-8')
    monkeypatch.setattr(pilot, 'preflight', lambda: frozen)
    monkeypatch.setattr(pilot, 'require_engine', lambda *a: True)
    grading = tmp_path / 'private' / 'old-dev'
    grading.mkdir(parents=True)
    monkeypatch.setattr(scorer, 'OUT', grading.parent)
    data = {'task.yaml': 'version: "1"\nlog_parser: pytest\n',
            'tests.json': '{"FAIL_TO_PASS":["failure"],"PASS_TO_PASS":["regression"]}',
            'gold.patch': 'PRIVATE_GOLD', 'test.patch': 'PRIVATE_TEST', 'eval.sh': 'SCORER_ONLY'}
    for name, value in data.items():
        (grading / name).write_text(value, encoding='utf-8')
    (grading / 'materialization.json').write_text(json.dumps({'instance_id': 'old-dev',
        'sha256': {name: pilot._sha(grading / name) for name in data}}), encoding='utf-8')
    task = {'instance_id': 'old-dev', 'image': 'official', 'repo': 'fixture', 'base_commit': 'a' * 40}
    monkeypatch.setattr(scorer, '_task', lambda _: (task, 'rev'))
    monkeypatch.setattr(scorer, '_official_grader', lambda: (
        lambda *a: ({'failure': 'PASSED'}, valid), lambda *a: p2p_ok,
        lambda *a: True, None, lambda **kwargs: SimpleNamespace(**kwargs)))
    commands = []

    def fake_docker(command, *, stdout, **kwargs):
        commands.append(command)
        assert command[command.index('--network') + 1] == 'none'
        assert '--pull=never' in command and '--cap-drop=ALL' in command
        assert 'git apply /candidate.patch' in command[-3] and 'gold.patch' not in command[-3]
        stdout.write(b'E1C2_SOURCE_IDENTITY:PASS' if identity else b'identity failed')
        return SimpleNamespace(returncode=rc)

    monkeypatch.setattr(pilot.subprocess, 'run', fake_docker)
    result = pilot.grade()
    assert len(commands) == 3 and all(r['resolved'] is resolved for r in result['rows'])
    assert result['official_feedback_sent_to_model'] is False
    pilot.verify_seal(root)
