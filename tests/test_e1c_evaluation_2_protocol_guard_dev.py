import pytest

from evals import e1c_evaluation_2_protocol_guard_dev as trial


def test_guard_is_on_actual_inner_execution_hook_and_restored(monkeypatch, tmp_path):
    compiled = trial.stage.pilot.previous.previous.method.base.base._compiled
    original = compiled.base.loop.execute_probe
    observed = []
    monkeypatch.setattr(trial, 'validate_frontier', lambda *args: observed.append('before execution') or {})
    with trial.configured(), compiled.configured():
        assert compiled.base.loop.execute_probe is not trial.stage.pilot.previous.adapter.execute_probe
        assert compiled.base.loop.parse_action is trial.stage.pilot.parse_action
        assert 'Shared setup executes in BOTH' in trial.stage.pilot.previous.adapter.POLICY
        assert compiled.preflight is trial.preflight and compiled.CAP == 40000
        # Guard rejects before delegate and before any execution; no synthetic container here.
        monkeypatch.setattr(trial, 'validate_frontier', lambda *args: (_ for _ in ()).throw(ValueError('binding missing')))
        with pytest.raises(ValueError, match='binding missing'):
            compiled.base.loop.execute_probe({}, {}, tmp_path, 'image', tmp_path / 'turn', {})
        assert not (tmp_path / 'turn').exists()
    assert compiled.base.loop.execute_probe is original and not observed
