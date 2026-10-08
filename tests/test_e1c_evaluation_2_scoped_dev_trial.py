import pytest

from evals import e1c_evaluation_2_scoped_dev_trial as trial


def value():
    return {'model': 'deepseek-flash', 'batch_token_cap': 50000, 'max_provider_calls': 16,
            'max_retries': 0, 'screen_denominator': 4}


def test_trial_is_a_new_identity_and_preserves_actual_scope_hook():
    method = trial.method
    before = method.OUT, method.PROTOCOL, method.preflight
    compiled = method.base.base._compiled
    with trial.configured(), compiled.configured():
        assert compiled.base.loop.execute_probe is method.execute_probe
        assert method.OUT == trial.OUT and method.OUT != trial.PARENT
        assert compiled.CAP == 50000 and compiled.TASK_CAP == 24000
        assert compiled.preflight is trial.preflight
    assert (method.OUT, method.PROTOCOL, method.preflight) == before


def test_trial_preflight_cannot_expand_budget_model_or_retry(monkeypatch):
    monkeypatch.setattr(trial, 'checked_parent', lambda: {})
    monkeypatch.setattr(trial, '_sha', lambda *args: 'digest')
    monkeypatch.setattr(trial, '_preflight', value)
    result = trial.preflight()
    assert result['real_provider_run_enabled'] and not result['repair_or_canary_authorized']


@pytest.mark.parametrize('change', [{'model': 'deepseek-pro'}, {'batch_token_cap': 100001}, {'max_retries': 1}, {'screen_denominator': 9}])
def test_trial_rejects_budget_or_scope_expansion(monkeypatch, change):
    monkeypatch.setattr(trial, 'checked_parent', lambda: {})
    monkeypatch.setattr(trial, '_preflight', lambda: {**value(), **change})
    with pytest.raises(ValueError, match='exact bounded Flash'):
        trial.preflight()
