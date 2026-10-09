import pytest

from evals import e1c_evaluation_2_completion_next_zero as method


@pytest.mark.parametrize('name,run', [('BOUNDARY', method.validate_boundary), ('LOCALIZE', method.localize)])
def test_zero_dispatch_does_not_repeat_started_identity(tmp_path, monkeypatch, name, run):
    monkeypatch.setattr(method, name, tmp_path)
    with pytest.raises(FileExistsError, match='started'):
        run()


def test_fresh_localization_uses_issue_and_base_only_not_cached_windows(tmp_path, monkeypatch):
    monkeypatch.setattr(method, 'ROOT', tmp_path)
    monkeypatch.setattr(method, 'LOCALIZE', tmp_path / 'new')
    monkeypatch.setattr(method, 'ISSUES', tmp_path / 'issues')
    monkeypatch.setattr(method, 'SOURCE', tmp_path / 'production')
    monkeypatch.setattr(method.parent.source, 'PARENT', tmp_path / 'original-parent')
    monkeypatch.setattr(method, 'source_bindings', lambda: {})
    monkeypatch.setattr(method, '_sha', lambda _: 'source-hash')
    tasks = [{'instance_id': 'a'}, {'instance_id': 'b'}]
    monkeypatch.setattr(method.parent, '_read', lambda p: {'tasks': tasks} if p.name == 'freeze.json' else {
        'base_commit': 'base', 'windows': 'FORBIDDEN_CACHED_WINDOWS'})
    for task in tasks:
        folder = method.ISSUES / task['instance_id']
        folder.mkdir(parents=True)
        (folder / 'problem_statement.md').write_text('PUBLIC_' + task['instance_id'], encoding='utf-8')
    calls = []

    def retrieve(issue, workspace, base, *, balanced):
        calls.append((issue, workspace, base, balanced))
        return {'status': 'ready_for_generation', 'windows': [{'path': 'module.py'}]}

    monkeypatch.setattr(method, 'freeze_input', retrieve)
    value = method.localize()
    assert [c[0] for c in calls] == ['PUBLIC_a', 'PUBLIC_b']
    assert all(c[2:] == ('base', True) for c in calls)
    assert value['end_to_end_reproducer_or_repair_complete'] is False
    assert value['manual_task_file_map'] is False
