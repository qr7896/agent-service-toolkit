from contextlib import nullcontext
from pathlib import Path

from evals import e1c_evaluation_2_completion_sweep_zero as method


def test_dispatch_freeze_is_not_mistaken_for_started_sweep(tmp_path, monkeypatch):
    monkeypatch.setattr(method, 'ROOT', tmp_path)
    monkeypatch.setattr(method, 'OUT', tmp_path / 'dispatch')
    monkeypatch.setattr(method, 'PROTOCOL', tmp_path / 'protocol.md')
    monkeypatch.setattr(method.paid, 'OUT', tmp_path / 'paid')
    monkeypatch.setattr(method.own, 'OUT', tmp_path / 'own')
    monkeypatch.setattr(method.paid, 'configured', nullcontext)
    monkeypatch.setattr(method.paid, 'preflight', lambda: {})
    monkeypatch.setattr(method.parent, 'verify_seal', lambda _: None)
    monkeypatch.setattr(method.parent, '_read', lambda p: {} if p.name == 'freeze.json' else {
        'unchanged_public_control_completed': True, 'unchanged_public_target_completed': True})
    monkeypatch.setattr(method, '_sha', lambda _: 'bound')

    def execute():
        assert method.sweep.OUT == tmp_path / 'dispatch/execution'
        assert not method.sweep.OUT.exists()
        assert (tmp_path / 'dispatch/dispatch-freeze.json').exists()
        assert method.parent.preflight() == {}
        return {'provider_calls': 0, 'phase_completed': {'patch': 21}}

    monkeypatch.setattr(method.sweep, 'run', execute)
    original = method.sweep.OUT
    assert method.run()['provider_calls'] == 0
    assert method.sweep.OUT == original and Path(tmp_path / 'dispatch/result.json').exists()
