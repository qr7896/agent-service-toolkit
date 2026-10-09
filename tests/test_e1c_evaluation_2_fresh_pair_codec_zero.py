import json

import pytest

from evals import e1c_evaluation_2_fresh_pair_codec_zero as audit


@pytest.fixture
def saved(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, 'ROOT', tmp_path)
    monkeypatch.setattr(audit, 'OUT', tmp_path / 'audit')
    monkeypatch.setattr(audit, 'PROTOCOL', tmp_path / 'protocol.md')
    monkeypatch.setattr(audit.parent, 'OUT', tmp_path / 'paid')
    for path in (audit.PROTOCOL, tmp_path / 'evals/e1c_evaluation_2_fresh_pair_codec_zero.py',
                 tmp_path / 'evals/e1c_evaluation_2_three_arm_decode_audit.py'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('fixture', encoding='utf-8')
    tasks = [{'instance_id': iid, 'image_id': 'fixture', 'input': {
        'production_windows': [], 'windows': [], 'base_commit': 'base', 'candidate_paths': ['module.py']}}
        for iid in ('library-a', 'library-b')]
    freeze = {'tasks': [{'instance_id': r['instance_id']} for r in tasks]}
    monkeypatch.setattr(audit.parent, 'preflight', lambda: freeze)
    monkeypatch.setattr(audit.parent, 'inputs', lambda: tasks)
    monkeypatch.setattr(audit.parent, 'require_engine', lambda *a: True)
    paid = audit.parent.OUT
    audit._save(paid / 'freeze.json', freeze)
    (paid / 'provider_calls.jsonl').write_text('sealed fixture ledger', encoding='utf-8')
    edit = {'path': 'module.py', 'old': 'unchanged old', 'new': 'unchanged model new'}
    for n, row in enumerate(tasks):
        root = paid / row['instance_id']
        audit._save(root / 'generation.json', {'operational_pair_valid': True, 'patch_written': bool(n)})
        audit._save(root / 'repair-call/response.json', {'raw': json.dumps(
            {'type': 'json_object', 'edits': [edit]} if n == 0 else {'edits': [edit]}), 'response_status': 'received'})
        for phase in ('normal', 'target'):
            audit._save(root / (phase + '-candidate.json'), {'source': phase, 'probe_sha256': phase})
    audit._save(paid / 'generation-seal.json', {'files': {p.relative_to(paid).as_posix(): audit._sha(p)
        for p in paid.rglob('*') if p.is_file()}, 'official_scoring_not_started': True})
    audit._save(paid / 'result.json', {'fixed_tasks': 2, 'rows': [{'instance_id': r['instance_id']} for r in tasks]})
    return paid, edit


def test_actual_zero_chain_preserves_code_and_seals_before_scoring_without_provider(saved, monkeypatch):
    paid, edit = saved
    before = {p.relative_to(paid).as_posix(): audit._sha(p) for p in paid.rglob('*') if p.is_file()}
    executions, scores = [], []

    def compile_patch(raw, body, workspace):
        assert json.loads(raw) == {'edits': [edit]}
        assert body['base_commit'] == 'base'
        return 'model patch fixture'

    monkeypatch.setattr(audit.parent.edits, 'compile_patch', compile_patch)

    def run_probe(candidate, row, root, patch):
        executions.append(candidate['source'])
        assert patch.read_text() == 'model patch fixture'
        return {'runs': [{'returncode': 0}, {'returncode': 0}]}

    monkeypatch.setattr(audit.parent, 'run_probe', run_probe)

    def grade(row, root):
        seal = audit.parent.edits._read(audit.OUT / 'generation-seal.json')
        assert seal['official_scoring_not_started']
        assert all(audit._sha(audit.OUT / p) == h for p, h in seal['files'].items())
        assert executions == ['normal', 'target']
        scores.append(row['instance_id'])
        return {'instance_id': row['instance_id'], 'resolved': True}

    monkeypatch.setattr(audit.parent, 'grade_one', grade)
    result = audit.run()
    assert result['provider_calls'] == 0 and result['newly_scored_candidates'] == 1
    assert scores == ['library-a'] and result['decoding'][1]['status'] == 'original_unchanged_not_rescored'
    assert result['full_issue_trusted'] is False and result['posthoc_not_original_frozen_score']
    assert before == {p.relative_to(paid).as_posix(): audit._sha(p) for p in paid.rglob('*') if p.is_file()}
    with pytest.raises(FileExistsError, match='no retry'):
        audit.run()


def test_parent_tamper_rejected_before_creating_zero_identity(saved):
    paid, _ = saved
    (paid / 'library-a/generation.json').write_text('{}', encoding='utf-8')
    with pytest.raises(ValueError, match='seal changed'):
        audit.run()
    assert not audit.OUT.exists()


def test_original_cohort_cannot_be_relabelled_or_missing(saved):
    paid, _ = saved
    (paid / 'result.json').write_text(json.dumps({'fixed_tasks': 3, 'rows': []}), encoding='utf-8')
    with pytest.raises(ValueError, match='completed original cohort'):
        audit.run()
    assert not audit.OUT.exists()
