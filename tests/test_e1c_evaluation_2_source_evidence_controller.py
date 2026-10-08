import copy
import hashlib

import pytest

from evals import e1c_evaluation_2_source_evidence_controller as controller


def fixture(tmp_path, monkeypatch, *, exposed=True):
    raw = b'class Api:\n    def __init__(self):\n        pass\n'
    (tmp_path / 'core.py').write_bytes(raw)
    window = {'path': 'core.py', 'source_sha256': hashlib.sha256(raw).hexdigest(), 'origin': 'public'}
    # Missing one definition is not missing ALL library context: the real runner
    # requires exposed production evidence before any model action.
    if not exposed:
        helper = tmp_path / 'core/helper.py'
        helper.parent.mkdir()
        helper.write_bytes(b'# exposed library context\n')
        context = {'path': 'core/helper.py', 'source_sha256': hashlib.sha256(helper.read_bytes()).hexdigest()}
    frozen = {'base_commit': 'b' * 40, 'windows': [window] if exposed else [context]}
    monkeypatch.setattr(controller.qualified, 'git_blob', lambda *args: raw)
    monkeypatch.setattr(controller, '_strict', lambda *args: {'production_bindings': [], 'unexposed_dependency_bindings': [],
                                                            'unknown': ['public_fixture_constraint_unproven'], 'rejected': ['existing_rejection']})
    payload = {'setup_source': 'import core\nobj = core.Api()', 'target_action': 'obj.run()'}
    return payload, frozen


def test_attribute_constructor_gets_source_bound_dependency_without_clearing_unknowns(tmp_path, monkeypatch):
    payload, frozen = fixture(tmp_path, monkeypatch)
    before = copy.deepcopy(frozen)
    result = controller.inspect_program(payload, frozen, tmp_path)
    assert result['production_bindings'][0]['symbol'] == 'Api'
    assert result['production_bindings'][0]['relation_type'] == 'qualified_call_dependency'
    assert result['unknown'] == ['public_fixture_constraint_unproven']
    assert result['rejected'] == ['existing_rejection'] and frozen == before


def test_missing_exposure_is_acquisition_request_not_mismatch(tmp_path, monkeypatch):
    payload, frozen = fixture(tmp_path, monkeypatch, exposed=False)
    result = controller.inspect_program(payload, frozen, tmp_path)
    assert result['production_bindings'] == []
    assert result['unexposed_dependency_bindings'] == [{'module': 'core', 'symbol': 'Api', 'path': 'core.py'}]
    assert 'unexposed_dependency_source_provenance_unknown' in result['unknown']


def test_changed_source_does_not_become_evidence(tmp_path, monkeypatch):
    payload, frozen = fixture(tmp_path, monkeypatch)
    (tmp_path / 'core.py').write_text('class Api:\n    pass\n')
    with pytest.raises(ValueError, match='differs from base'):
        controller.inspect_program(payload, frozen, tmp_path)


def test_alias_wrong_definition_never_clears_prior_rejection(tmp_path, monkeypatch):
    payload, frozen = fixture(tmp_path, monkeypatch)
    payload['setup_source'] = 'import core\nobj = core.Other()'
    result = controller.inspect_program(payload, frozen, tmp_path)
    assert not result['production_bindings'] and result['rejected'] == ['existing_rejection']
    assert 'qualified_attribute_definition_unknown' in result['unknown']


def test_external_helper_not_misclassified_as_missing_production(tmp_path, monkeypatch):
    payload, frozen = fixture(tmp_path, monkeypatch)
    payload['setup_source'] = 'import numpy as np\nx = np.array([1])'
    result = controller.inspect_program(payload, frozen, tmp_path)
    assert result['unknown'] == ['public_fixture_constraint_unproven']
    assert result['production_bindings'] == []


def test_rank_is_generic_requested_then_attributes_with_two_file_cap(tmp_path, monkeypatch):
    _, frozen = fixture(tmp_path, monkeypatch)
    for name in ('helper', 'field'):
        raw = b'def f():\n    return 1\n'
        (tmp_path / (name + '.py')).write_bytes(raw)
        frozen['windows'].append({'path': name + '.py', 'source_sha256': hashlib.sha256(raw).hexdigest(),
                                  'origin': 'agent_module_name_hint' if name == 'helper' else 'public'})
    monkeypatch.setattr(controller.qualified, 'git_blob', lambda workspace, base, name: (workspace / name).read_bytes())
    program = {'production_bindings': [{'path': 'core.py'}, {'path': 'field.py', 'relation_type': 'qualified_call_dependency'}]}
    assert [s['path'] for s in controller.ranked_sites(frozen, tmp_path, program)] == ['helper.py', 'field.py']


def test_actual_nested_policy_qualification_and_observer_hooks_restore():
    original = controller.qualified.inspect_program, controller.bounded.inspect_program, controller.qualified.observe
    with controller.configured() as compiled, compiled.configured():
        assert controller.qualified.inspect_program is controller.inspect_program
        assert controller.bounded.inspect_program is controller.inspect_program
        assert controller.qualified.observe is controller.observe
        assert compiled.base.loop.retrieve is controller.previous.retrieve
        assert compiled.base.loop.parse_action is controller.previous.previous.previous.stage.pilot.parse_action
    assert original == (controller.qualified.inspect_program, controller.bounded.inspect_program, controller.qualified.observe)
