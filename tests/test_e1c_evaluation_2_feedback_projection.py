import copy

import pytest

from evals import e1c_evaluation_2_feedback_projection as projection
from evals.e1c_blind_boundary import BlindBoundaryViolation


def feedback():
    return {'status': 'evidence_required_before_selection', 'scope_gate': {'repair_eligible': False, 'missing': ['source']},
            'controller_verdict': {'qualification': {'schema': 'e1c2-bounded-qualification-v2', 'Gold_used': False, 'unknown': ['source']},
                                   'behavior': {'schema': 'e1c2-bounded-behavior-gate-v1', 'Gold_used': False, 'trusted_reproducer': False}}}


def test_only_known_false_flags_removed_without_mutation_or_scope_upgrade():
    value = feedback()
    before = copy.deepcopy(value)
    projected = projection.project_feedback(value)
    assert value == before
    assert projected['scope_gate'] == value['scope_gate'] and projected['status'] == value['status']
    assert projected['controller_verdict']['qualification']['unknown'] == ['source']
    assert 'Gold_used' not in projected['controller_verdict']['qualification']
    assert 'Gold_used' not in projected['controller_verdict']['behavior']


@pytest.mark.parametrize('flag', [True, None, 0, 'false'])
def test_evaluator_or_untyped_metadata_cannot_be_projected(flag):
    value = feedback()
    value['controller_verdict']['qualification']['Gold_used'] = flag
    with pytest.raises(ValueError, match='metadata'):
        projection.project_feedback(value)


def test_unknown_schema_cannot_remove_metadata():
    value = feedback()
    value['controller_verdict']['qualification']['schema'] = 'invented'
    with pytest.raises(ValueError, match='metadata'):
        projection.project_feedback(value)


@pytest.mark.parametrize('change', [{'observed_trace': 'gold.patch expected answer'}, {'another': {'Gold_used': False}}])
def test_real_marker_or_unrecognized_location_still_rejected(change):
    with pytest.raises(BlindBoundaryViolation):
        projection.project_feedback({**feedback(), **change})


def test_actual_hook_projects_feedback_but_preserves_oracle_candidate_execution(tmp_path, monkeypatch):
    candidate, oracle, execution = {}, {}, {}
    monkeypatch.setattr(projection, '_execute', lambda *args: (feedback(), oracle, candidate, execution))
    public, lock, selected, runs = projection.execute_probe({}, {}, tmp_path, 'image', tmp_path, {})
    assert lock is oracle and selected is candidate and runs is execution
    assert public['scope_gate']['repair_eligible'] is False


def test_nested_configuration_preserves_projection_hook_and_restores_owner():
    from evals import e1c_evaluation_2_scoped_dev_trial as trial
    before = trial.method.execute_probe
    with projection.configured(), trial.configured(), trial.method.base.base._compiled.configured():
        assert trial.method.base.base._compiled.base.loop.execute_probe is projection.execute_probe
    assert trial.method.execute_probe is before
