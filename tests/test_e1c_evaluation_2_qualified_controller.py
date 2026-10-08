import copy
import hashlib
import json

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from evals import e1c_evaluation_2_behavior_gate as behavior
from evals import e1c_evaluation_2_qualified_controller as controller


def fixture(tmp_path, monkeypatch):
    source = b'class Api:\n    def __init__(self, count=1):\n        """Parameters\n        ----------\n        count : int, default=1\n\n        Examples\n        --------\n        assert answer == 99\n        """\n        pass\n'
    (tmp_path / 'core.py').write_bytes(source)
    monkeypatch.setattr(controller, 'git_blob', lambda *args: source)
    monkeypatch.setattr(behavior, 'git_blob', lambda *args: source)
    quote = 'Please expose `flag` in `core.Api.__init__()`.\n'
    frozen = {'base_commit': 'b' * 40, 'issue': quote + 'flag : bool, optional\n',
              'windows': [{'path': 'core.py', 'symbol': '__init__', 'owner': 'Api', 'source_sha256': hashlib.sha256(source).hexdigest()}]}
    payload = {'setup_source': 'from core import Api', 'control_action': 'Api(count=1)', 'target_action': 'Api(count=1, flag=True)',
               'issue_quote': quote, 'expected_quote': quote, 'oracle': 'call_completes', 'assertion': ''}
    return payload, frozen


def test_contract_augmented_messages_preserve_original_and_exclude_examples(tmp_path, monkeypatch):
    _, frozen = fixture(tmp_path, monkeypatch)
    original = {'windows': frozen['windows'], 'public_issue_catalogue': 'public only'}
    monkeypatch.setattr(controller, '_messages', lambda *args: [SystemMessage(content='policy'), HumanMessage(content=json.dumps(original))])
    token = controller._workspaces.set({frozen['base_commit']: tmp_path})
    try:
        value = controller.messages(frozen)
    finally:
        controller._workspaces.reset(token)
    body = json.loads(value[1].content)
    assert all(body[k] == v for k, v in original.items())
    assert body['production_parameter_contracts'][0]['declarations'][0]['parameter'] == 'count'
    assert 'answer' not in str(body) and 'Examples' not in str(body)


def test_missing_verified_workspace_is_not_inferred_from_task_id(tmp_path, monkeypatch):
    _, frozen = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(controller, '_messages', lambda *args: [SystemMessage(content='policy'), HumanMessage(content='{}')])
    token = controller._workspaces.set({})
    try:
        with pytest.raises(ValueError, match='verified input loader'):
            controller.messages(frozen)
    finally:
        controller._workspaces.reset(token)


@pytest.mark.parametrize('change', [{'assertion': 'assert True'}, {'expected_quote': 'invented promise'},
                                  {'setup_source': 'from core import Api\nApi = other'}])
def test_policy_rejects_before_delegate(tmp_path, monkeypatch, change):
    payload, frozen = fixture(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(controller, '_execute', lambda *args: calls.append(args))
    result = controller.execute_probe({**payload, **change}, frozen, tmp_path, 'image', tmp_path / 'turn', {'missing_optional_import': None})
    assert result[0]['status'] == 'action_rejected' and not calls
    assert (tmp_path / 'turn/controller-admission.json').is_file()


def test_changed_exposed_source_stops_before_execution(tmp_path, monkeypatch):
    payload, frozen = fixture(tmp_path, monkeypatch)
    (tmp_path / 'core.py').write_bytes(b'class Api: pass\n')
    with pytest.raises(ValueError, match='source identity'):
        controller.policy(payload, frozen, tmp_path)


def test_delegate_observation_qualification_behavior_are_one_controller_chain(tmp_path, monkeypatch):
    payload, frozen = fixture(tmp_path, monkeypatch)
    before = copy.deepcopy((payload, frozen))
    source = payload['setup_source'] + '\n' + payload['target_action'] + '\n'
    candidate = {'source': source, 'probe_sha256': hashlib.sha256(source.encode()).hexdigest()}
    execution = {'runs': [{'returncode': 1, 'timed_out': False}, {'returncode': 1, 'timed_out': False}]}
    calls = []

    def delegate(*args):
        calls.append('delegate')
        root = args[4]
        controller._save(root / 'compiler.json', {'canonical_contract': payload})
        for n in (1, 2):
            controller._save(root / f'control-{n}.json', {'runs': [{'returncode': 0, 'timed_out': False}]})
        return {'status': 'base_witness_semantics_unverified'}, {'locked': True}, candidate, execution

    def observer(*args, **kwargs):
        calls.append('observer')
        assert args[0] is candidate and kwargs['keywords'] == ['flag']
        return {'schema': 'e1c2-source-bound-exception-observation-v2', 'original_probe_sha256': candidate['probe_sha256'],
                'canonical_git_and_effective_file_hash_required': True, 'returncode': 1,
                'records': [{'scope': 'owned_probe', 'path': '/e1c2_model_probe.py', 'line': 2,
                             'exception_type': 'builtins.TypeError', 'declared_missing_keyword': 'flag'}]}

    monkeypatch.setattr(controller, '_execute', delegate)
    monkeypatch.setattr(controller, 'observe', observer)
    result = controller.execute_probe(payload, frozen, tmp_path, 'image', tmp_path / 'turn', {'missing_optional_import': None})
    verdict = result[0]['controller_verdict']
    assert calls == ['delegate', 'observer']
    assert verdict['qualification']['status'] == 'mechanism_supported_candidate'
    assert verdict['behavior']['sub_obligation_supported']
    assert not verdict['trusted_reproducer'] and result[2] is candidate and result[3] is execution
    assert (payload, frozen) == before


def test_unselected_execution_does_not_create_observer(tmp_path, monkeypatch):
    payload, frozen = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(controller, '_execute', lambda *args: ({'status': 'control_failed'}, None, None, None))
    monkeypatch.setattr(controller, 'observe', lambda *args, **kwargs: pytest.fail('observer not allowed'))
    assert controller.execute_probe(payload, frozen, tmp_path, 'image', tmp_path / 'turn', {'missing_optional_import': None})[2] is None


def test_actual_nested_runner_hooks_restore_and_do_not_change_old_namespace():
    compiled = controller.base._compiled
    before = compiled.execute_probe, compiled.base.loop.execute_probe, compiled.base.loop.messages, controller.base.OUT
    with controller.configured():
        with compiled.configured():
            assert compiled.execute_probe is controller.execute_probe
            assert compiled.base.loop.execute_probe is controller.execute_probe
            assert compiled.base.loop.messages is controller.messages
            assert compiled.CAP == 50000
    assert (compiled.execute_probe, compiled.base.loop.execute_probe, compiled.base.loop.messages, controller.base.OUT) == before


def test_configuration_failure_restores_global_owners_and_workspace_routes():
    compiled = controller.base._compiled
    before = compiled.execute_probe, compiled.base.loop.execute_probe, controller._workspaces.get()
    with pytest.raises(RuntimeError):
        with controller.configured():
            with compiled.configured():
                raise RuntimeError('synthetic adapter failure')
    assert (compiled.execute_probe, compiled.base.loop.execute_probe, controller._workspaces.get()) == before


def test_synthetic_issue_does_not_inherit_real_fixture_obligations():
    initial = {'issue': 'real issue', 'issue_sha256': 'old', 'public_fixture_facts': [{'facts': ['real']}],
               'base_commit': 'base', 'windows': [{'path': 'production.py'}]}
    before = copy.deepcopy(initial)
    synthetic = controller.synthetic_input(initial)
    assert initial == before
    assert synthetic['windows'] is initial['windows'] and synthetic['base_commit'] == 'base'
    assert synthetic['public_fixture_facts'] == []
    assert synthetic['issue_sha256'] == hashlib.sha256(synthetic['issue'].encode()).hexdigest()
    assert controller.base.report_anchors(synthetic['issue'])['anchors'][0]['kind'] == 'regression_report'
