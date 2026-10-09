import pytest

from evals import e1c_evaluation_2_issue_reference_zero as method


def test_references_require_qualified_literal_and_preserve_order_not_task_ids():
    issue = '`package.Class` and `other.module.Function`, `package.Class`; https://secret.example/x; `not-qualified`'
    assert method.references(issue) == ['package.Class', 'other.module.Function']


def test_unresolved_public_reference_remains_unknown(monkeypatch):
    monkeypatch.setattr(method, 'resolve_symbol', lambda *args: None)
    monkeypatch.setattr(method, 'audit_repair_visible_payload', lambda _: None)
    view = {'issue': '`package.Class`', 'base_commit': 'base', 'windows': []}
    result, rows, added = method.supplement(view, None)
    assert added == 0 and result['windows'] == []
    assert rows[0]['status'] == 'unresolved' and rows[0]['semantic_binding_certified'] is False


def test_started_supplement_never_repeats(tmp_path, monkeypatch):
    monkeypatch.setattr(method, 'OUT', tmp_path)
    with pytest.raises(FileExistsError, match='started'):
        method.run()
