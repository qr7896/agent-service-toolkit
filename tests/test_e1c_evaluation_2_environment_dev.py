import copy

import pytest

from evals import e1c_evaluation_2_environment_dev as trial


def test_actual_nested_environment_hook_policy_and_budget_restore():
    compiled = trial.previous.stage.pilot.previous.previous.method.base.base._compiled
    before = compiled.configured, compiled.base.loop.execute_probe, trial.previous.POLICY
    with trial.configured(), compiled.configured():
        assert compiled.base.loop.parse_action is trial.previous.stage.pilot.parse_action
        assert compiled.preflight is trial.preflight and compiled.CAP == 40000 and compiled.TASK_CAP == 24000
        assert trial.previous.stage.pilot.previous.adapter.POLICY == trial.POLICY
        assert 'legitimate failing entrypoint' in trial.POLICY
    assert before == (compiled.configured, compiled.base.loop.execute_probe, trial.previous.POLICY)


def test_projection_preserves_oracle_candidate_execution_and_unknown(monkeypatch, tmp_path):
    import json
    row = {'schema': 'e1c-evaluation-2-probe-execution-v1', 'input_sha256': 'i', 'image': 'image', 'base_commit': 'b',
           'missing_optional_import': 'optional', 'network_none': True, 'pull_never': True,
           'runs': [{'returncode': 0, 'timed_out': False}]}
    for n in (1, 2):
        (tmp_path / f'control-{n}.json').write_text(json.dumps(row))
    original = {'status': 'evidence_required_before_selection', 'scope_gate': {'repair_eligible': False, 'missing': ['scope']}}
    before = copy.deepcopy(original)
    locked, candidate = {'locked': True}, {'selected': False}
    result = trial.annotate((original, locked, candidate, row), tmp_path)
    assert result[0]['own_executor_environment']['module'] == 'optional'
    assert result[1] is locked and result[2] is candidate and result[3] is row
    assert result[0]['scope_gate'] == before['scope_gate'] and original == before


def test_unknown_environment_does_not_become_absence(tmp_path):
    result = ({'status': 'control_failed'}, None, None, None)
    assert trial.annotate(result, tmp_path) is result
    result = ({}, {}, None, {'missing_optional_import': None})
    assert trial.annotate(result, tmp_path) is result


def test_changed_parent_identity_stops_before_provider(monkeypatch, tmp_path):
    import json
    monkeypatch.setattr(trial, 'PARENT', tmp_path)
    (tmp_path / 'freeze.json').write_text(json.dumps({'method_sha256': {'source.py': 'original'}, 'protocol_sha256': 'original'}))
    (tmp_path / 'generation-seal.json').write_text(json.dumps({'files': {}}))
    monkeypatch.setattr(trial, '_sha', lambda *args: 'not the original digest')
    with pytest.raises(ValueError, match='parent changed'):
        trial.checked_parent()
