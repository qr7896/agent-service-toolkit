from contextlib import nullcontext

import pytest

from evals import e1c_evaluation_2_completion_validation_zero as method


def test_started_zero_validation_does_not_repeat_container_or_model(tmp_path, monkeypatch):
    monkeypatch.setattr(method, 'OUT', tmp_path)
    monkeypatch.setattr(method.paid, 'configured', lambda: pytest.fail('must stop before hooks'))
    with pytest.raises(FileExistsError, match='started'):
        method.run()


def test_zero_validation_rejects_unresolved_without_creating_namespace(tmp_path, monkeypatch):
    monkeypatch.setattr(method, 'OUT', tmp_path / 'new')
    monkeypatch.setattr(method.paid, 'configured', nullcontext)
    monkeypatch.setattr(method.paid, 'preflight', lambda: {})
    monkeypatch.setattr(method.parent, 'verify_seal', lambda _: None)
    monkeypatch.setattr(method.parent, '_read', lambda p: {} if p.name == 'freeze.json' else {
        'fixed_cells': 1, 'rows': [{'resolved': False}]})
    with pytest.raises(ValueError, match='actually resolved'):
        method.run()
    assert not method.OUT.exists()
