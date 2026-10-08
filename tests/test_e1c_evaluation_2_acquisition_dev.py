import pytest

from evals import e1c_evaluation_2_acquisition_dev as trial


def test_actual_nested_runner_uses_new_budget_input_and_acquisition_hooks():
    compiled = trial.previous.method.base.base._compiled
    before = compiled.CAP, compiled.TASK_CAP, compiled.base.loop.CONTEXT_CAP
    with trial.configured(), compiled.configured():
        assert compiled.CAP == 80000 and compiled.TASK_CAP == 48000 and compiled.OUTPUT_CAP == 2000
        assert compiled.base.loop.CONTEXT_CAP == 96000
        assert compiled.base.loop.execute_probe is trial.adapter.execute_probe
        assert compiled.base.loop.messages is trial.adapter.messages and compiled.conversation is trial.adapter.conversation
        assert compiled.preflight is trial.preflight
    assert (compiled.CAP, compiled.TASK_CAP, compiled.base.loop.CONTEXT_CAP) == before


def test_preflight_reports_soft_and_hard_budgets_but_no_canary(monkeypatch):
    monkeypatch.setattr(trial.previous, 'checked_parent', lambda: {})
    monkeypatch.setattr(trial, 'checked_zero', lambda: {})
    monkeypatch.setattr(trial, '_sha', lambda *args: 'digest')
    monkeypatch.setattr(trial, '_preflight', lambda: {'batch_token_cap': 80000, 'task_token_cap': 48000, 'model': 'deepseek-flash'})
    value = trial.preflight()
    assert value['input_hard_tokens'] == 24000 and value['task_soft_token_target'] == 32000
    assert value['real_provider_run_enabled'] and not value['repair_or_canary_authorized']


def test_inherited_old_budget_cannot_silently_run(monkeypatch):
    monkeypatch.setattr(trial.previous, 'checked_parent', lambda: {})
    monkeypatch.setattr(trial, 'checked_zero', lambda: {})
    monkeypatch.setattr(trial, '_preflight', lambda: {'batch_token_cap': 50000, 'task_token_cap': 24000, 'model': 'deepseek-flash'})
    with pytest.raises(ValueError, match='actual runner'):
        trial.preflight()
