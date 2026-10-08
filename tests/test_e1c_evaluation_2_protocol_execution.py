import ast

import pytest

from evals import e1c_evaluation_2_protocol_execution as guard


def test_frontier_never_executes_or_invents_missing_control_receiver(monkeypatch):
    payload = {'setup_source': 'import core\nx = [1]\nmodel = core.Api(new=True)', 'control_action': 'model.fit(x)'}
    monkeypatch.setattr(guard, 'rephase_setup', lambda *args: ({**payload, 'setup_source': 'import core\nx = [1]'},
                                                           {'moved_from_line': 3}))
    with pytest.raises(ValueError, match='compiler_frontier_removes_control_binding:model'):
        guard.validate_frontier(payload, {}, None)
    assert payload['control_action'] == 'model.fit(x)'  # no fabricated normal control


def test_control_can_explicitly_define_its_own_supported_receiver(monkeypatch):
    payload = {'setup_source': 'import core\nx = [1]\nmodel = core.Api(new=True)',
               'control_action': 'model = core.Api()\nmodel.fit(x)'}
    monkeypatch.setattr(guard, 'rephase_setup', lambda *args: ({**payload, 'setup_source': 'import core\nx = [1]'},
                                                           {'moved_from_line': 3}))
    assert guard.validate_frontier(payload, {}, None)['compiler_removed_control_bindings'] == []


def test_no_frontier_and_top_level_bindings(monkeypatch):
    assert guard.bindings(ast.parse('import core as c\nfrom x import Api as A\nx, y = (1, 2)').body) == {'c', 'A', 'x', 'y'}
    payload = {'setup_source': 'x = 1', 'control_action': 'print(x)'}
    monkeypatch.setattr(guard, 'rephase_setup', lambda *args: (payload, {'moved_from_line': None}))
    assert guard.validate_frontier(payload, {}, None)['changed_probe'] is False


@pytest.mark.parametrize('control', ['model = model.copy()', 'if flag:\n    model = core.Api()\nmodel.fit(x)'])
def test_unknown_self_reference_or_conditional_binding_is_not_proven(monkeypatch, control):
    payload = {'setup_source': 'import core\nmodel = core.Api(new=True)', 'control_action': control}
    monkeypatch.setattr(guard, 'rephase_setup', lambda *args: ({**payload, 'setup_source': 'import core'}, {'moved_from_line': 2}))
    with pytest.raises(ValueError, match='compiler_frontier_removes_control_binding'):
        guard.validate_frontier(payload, {}, None)
