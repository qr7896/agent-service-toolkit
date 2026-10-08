"""Fresh Controller adapter: public contracts, source identity and bounded verdicts."""

from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import json
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agents.model_budget import ProviderBudgetExceeded
from evals import e1c_evaluation_2_report_anchor_dev as base
from evals.e1c_blind_boundary import assert_agent_path
from evals.e1c_evaluation_2_api_obligation import obligations
from evals.e1c_evaluation_2_behavior_gate import assess
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_exception_observer import public_message_hashes
from evals.e1c_evaluation_2_exception_observer_v2 import observe, project_sites
from evals.e1c_evaluation_2_issue_quote_refs import catalogue
from evals.e1c_evaluation_2_parameter_contract import parameter_declarations
from evals.e1c_evaluation_2_qualification_v2 import inspect_program, qualify
from evals.e1c_evaluation_2_qualification_v3 import git_blob
from evals.e1c_strict_v5_boundary import (
    assert_production_relative_path,
    audit_repair_visible_payload,
)

OUT = ROOT / '.codex/e1c/evaluation_2/qualified-controller-dev-v1'
SMOKE = ROOT / '.codex/e1c/evaluation_2/qualified-controller-zero-smoke-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_QUALIFIED_CONTROLLER_V1_PROTOCOL_2026-10-08.md'
MODULES = (*base.MODULES, 'evals/e1c_evaluation_2_qualified_controller.py', 'evals/e1c_evaluation_2_behavior_gate.py',
           'evals/e1c_evaluation_2_parameter_contract.py', 'evals/e1c_evaluation_2_qualification.py',
           'evals/e1c_evaluation_2_qualification_v2.py', 'evals/e1c_evaluation_2_qualification_v3.py',
           'evals/e1c_evaluation_2_exception_observer.py', 'evals/e1c_evaluation_2_exception_observer_v2.py',
           'evals/e1c_evaluation_2_guard_type_observer.py')
_execute, _messages, _configured = base.execute_probe, base.messages, base.configured
_preflight = base.preflight
_workspaces = ContextVar('qualified_controller_workspaces', default={})


def source_contracts(frozen, workspace):
    records, trees = [], {}
    for row in frozen['windows']:
        name = assert_production_relative_path(row['path'])
        path = assert_agent_path(workspace / name, workspace=workspace)
        if path.stat().st_size > 1_000_000:
            raise ValueError('bounded production source required')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != row['source_sha256'] or raw.replace(b'\r\n', b'\n') != git_blob(workspace, frozen['base_commit'], name):
            raise ValueError('Controller source identity differs from exposure/canonical base')
        trees.setdefault(name, ast.parse(raw))
        for node in ast.walk(trees[name]):
            if not isinstance(node, ast.FunctionDef) or node.name != row.get('symbol'):
                continue
            owner = row.get('owner')
            if owner and not any(isinstance(c, ast.ClassDef) and c.name == owner and node in c.body for c in ast.walk(trees[name])):
                continue
            parameters = [a.arg for a in (*node.args.args, *node.args.kwonlyargs) if a.arg not in {'self', 'cls'}][:8]
            declarations = parameter_declarations(node, parameters)
            if declarations:
                item = {'path': name, 'source_sha256': row['source_sha256'], 'symbol': node.name, 'owner': owner,
                        'declarations': declarations, 'relation_type': 'parameter_contract', 'origin': 'frozen_production_definition',
                        'depth': 0, 'does_not_override_explicit_public_change_request': True}
                if item not in records:
                    records.append(item)
    audit_repair_visible_payload(records)
    return records[:8]


def messages(frozen, feedback=None, previous=None):
    value = _messages(frozen, feedback, previous)
    # Generation only sees public source parameter declarations, never prior scores/probes.
    workspace = _workspaces.get().get(frozen['base_commit'])
    if workspace is None:
        raise ValueError('Controller workspace must be bound by verified input loader')
    body = json.loads(value[1].content)
    body['production_parameter_contracts'] = source_contracts(frozen, workspace)
    audit_repair_visible_payload(body)
    text = json.dumps(body, ensure_ascii=False)
    if len(text) > 30000:
        raise ProviderBudgetExceeded('contract-augmented context exceeds frozen character cap')
    value[1] = HumanMessage(content=text)
    value[0] = SystemMessage(content=value[0].content + ' Separate explicit public change requests from base API documentation and completion hypotheses. '
        'A normal API accepting a type does not prove target API support. Preserve unknowns, retrieve missing production definitions, '
        'and do not treat a keyword-acceptance sub-obligation as default behavior or incremental functionality. Parameter declarations exclude examples and test oracles.')
    return value


def policy(payload, frozen, workspace):
    contracts = source_contracts(frozen, workspace)
    program = inspect_program(payload, frozen, workspace)
    spans = catalogue(frozen['issue'])['spans']
    anchors = [a for a in base.report_anchors(frozen['issue'])['anchors'] if spans[a['quote_ref']]['text'] == payload['expected_quote']]
    reasons = list(program['rejected'])
    if len(anchors) != 1:
        reasons.append('unique_public_expectation_origin_unproven')
    if payload['oracle'] != 'call_completes' or payload['assertion'] != '':
        reasons.append('oracle_outside_completion_scope')
    return {'schema': 'e1c2-qualified-controller-policy-v1', 'decision': 'REJECT' if reasons else 'EXECUTE_UNCERTIFIED_DEV_CANDIDATE',
            'reasons': sorted(set(reasons)), 'program': program, 'parameter_contracts': contracts,
            'expectation_origin': anchors[0]['kind'] if len(anchors) == 1 else None, 'trusted_reproducer': False}


def execute_probe(payload, frozen, workspace, image, root, environment, locked=None):
    admission = policy(payload, frozen, workspace)
    _save(root / 'controller-admission.json', admission)
    if admission['decision'] == 'REJECT':
        return {'status': 'action_rejected', 'reason': 'Controller_policy_rejected', 'controller_reasons': admission['reasons']}, locked, None, None
    feedback, oracle, candidate, execution = _execute(payload, frozen, workspace, image, root, environment, locked)
    if candidate is None:
        _save(root / 'controller-verdict.json', {'status': 'execution_not_selected', 'feedback_status': feedback['status'], 'trusted_reproducer': False})
        return feedback, oracle, candidate, execution
    canonical = json.loads((root / 'compiler.json').read_bytes())['canonical_contract']
    program = inspect_program(canonical, frozen, workspace)
    paths = list(dict.fromkeys(r['path'] for r in program['production_bindings']))
    if not paths or program['rejected']:
        verdict = {'status': 'unknown_or_rejected_dependency_evidence', 'program': program, 'trusted_reproducer': False}
    else:
        hashes = {r['path']: r['source_sha256'] for r in frozen['windows']}
        sites = [{'path': path, 'line': 1, 'variable': 'exception', 'source_sha256': hashes[path]} for path in paths[:2]]
        # line=1 is a file-identity observation boundary, not a claimed failing guard.
        projected, proofs = project_sites(workspace, sites)
        probe = root / 'execution' / (candidate['probe_sha256'] + '.py')
        blocker = root / 'execution/optional_missing' if environment['missing_optional_import'] else None
        observation = observe(candidate, probe, projected, image, frozen['base_commit'], root / 'controller-observation',
                              public_hashes=public_message_hashes(frozen['issue']), keywords=[c['parameter'] for c in obligations(frozen['issue'])],
                              blocked_import_dir=blocker)
        controls = [json.loads((root / f'control-{n}.json').read_bytes()) for n in (1, 2)]
        normal = all(len(c.get('runs', [])) == 1 and type(c['runs'][0].get('returncode')) is int and c['runs'][0]['returncode'] == 0
                     and not c['runs'][0].get('timed_out') for c in controls)
        target = len(execution.get('runs', [])) == 2 and all(type(r.get('returncode')) is int and r['returncode'] == 1 and not r.get('timed_out') for r in execution['runs'])
        qualification = qualify(canonical, frozen, workspace, candidate, observation, normal_controls_pass=normal, target_repeatable_failure=target)
        behavior = assess(canonical, frozen, workspace, candidate, observation, qualification)
        verdict = {'status': 'controller_qualification_recorded', 'qualification': qualification, 'behavior': behavior,
                   'source_projection': proofs, 'diagnostic_scope': 'first_two_needed_production_files_only', 'trusted_reproducer': False}
    _save(root / 'controller-verdict.json', verdict)
    if program['rejected']:
        return {**feedback, 'status': 'action_rejected', 'controller_verdict': verdict}, oracle, None, execution
    return {**feedback, 'controller_verdict': verdict}, oracle, candidate, execution


@contextmanager
def configured():
    with ExitStack() as stack:
        for key, value in [('OUT', OUT), ('SMOKE', SMOKE), ('PROTOCOL', PROTOCOL), ('MODULES', MODULES), ('messages', messages), ('preflight', preflight)]:
            stack.enter_context(patch.object(base, key, value))
        stack.enter_context(_configured())
        original_inputs = base._compiled.inputs
        token = _workspaces.set({})
        stack.callback(_workspaces.reset, token)

        def inputs():
            rows = original_inputs()
            routes = {}
            for _, frozen, workspace in rows:
                commit = frozen['base_commit']
                if commit in routes and routes[commit] != workspace:
                    raise ValueError('ambiguous verified workspace/base binding')
                routes[commit] = workspace
            _workspaces.set(routes)
            return rows

        stack.enter_context(patch.object(base._compiled, 'inputs', inputs))
        stack.enter_context(patch.object(base._compiled, 'execute_probe', execute_probe))
        stack.enter_context(patch.object(base._compiled.base.loop, 'execute_probe', execute_probe))
        stack.enter_context(patch.object(base._compiled.base.loop, 'messages', messages))
        yield


def preflight():
    value = _preflight()
    return {**value, 'schema': 'e1c2-qualified-controller-four-reference-dev-v1',
            'Controller_policy_execution_qualification_hook': True, 'parameter_contract_context': True,
            'automatic_exception_observation_per_selected_candidate': True, 'diagnostic_files_limit': 2,
            'full_issue_trust_gate_passed': False, 'real_provider_run_enabled': False}


async def smoke():
    if SMOKE.exists():
        raise FileExistsError('qualified Controller smoke already started; no retry')
    from evals.e1c_evaluation_2_container_health import require_engine
    with configured():
        rows = base._compiled.inputs()
        require_engine(tuple(t['image_id'] for t, _, _ in rows))
        _save(SMOKE / 'freeze.json', {'modules': {n: _sha(ROOT / n) for n in MODULES}, 'provider_calls': 0,
                                   'protocol_sha256': _sha(PROTOCOL), 'synthetic_not_task_score': True})
        # Reuse the existing two library positive fixtures; never real-task policy rules.
        examples = [('sklearn', 'IsolationForest', 'from sklearn.ensemble import IsolationForest', 'IsolationForest(n_estimators=2, random_state=0)'),
                    ('marshmallow', 'Schema', 'from marshmallow import Schema', 'Schema(only=[]).dump({})')]
        reports = []
        for library, symbol, setup, call in examples:
            eligible = [(task, initial, workspace) for task, initial, workspace in rows if any(
                w['path'].removeprefix('src/').startswith(library + '/') for w in initial['windows'])]
            if not eligible:
                raise ValueError('existing synthetic library control source unavailable')
            task, initial, workspace = eligible[0]
            synthetic = synthetic_input(initial)
            quote = synthetic['issue']
            payload = {'issue_quote': quote, 'expected_quote': quote, 'oracle': 'call_completes', 'assertion': '',
                       'setup_source': setup, 'control_action': call, 'target_action': call}
            actions = [{'retrieve': symbol}, {'probe': payload}, {'abstain_reason': 'supported synthetic call is not a failure witness'}]
            observed = []

            async def invoke(msgs, turn):
                observed.append(json.loads(msgs[-1].content)['last_feedback'])
                return AIMessage(content=json.dumps(actions[turn - 1]), usage_metadata={'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0})

            folder = SMOKE / library
            result = await base._compiled.base.loop.run_task(synthetic, workspace, task['image_id'], folder, task['environment'], invoke)
            controls = [json.loads((folder / 'turn-2' / f'control-{n}.json').read_bytes()) for n in (1, 2)]
            admission = json.loads((folder / 'turn-2/controller-admission.json').read_bytes())
            verdict = json.loads((folder / 'turn-2/controller-verdict.json').read_bytes())
            passed = all(base._compiled.base.loop.checked_execution(c) for c in controls)
            if not passed or result['status'] != 'abstained' or observed[-1]['status'] != 'target_not_repeatable_failure' or admission['decision'] != 'EXECUTE_UNCERTIFIED_DEV_CANDIDATE':
                raise ValueError('qualified Controller positive chain failed')
            reports.append({'library_fixture': library, 'controls_pass': True, 'inner_Controller_policy_seen': True,
                            'post_execution_verdict_seen': verdict['status'] == 'execution_not_selected', 'feedback_consumed': True,
                            'not_selected_as_bug': True, 'provider_calls': 0})
        value = {'schema': 'e1c2-qualified-controller-zero-smoke-v1', 'cross_repository_positive_control_gate': len(reports) == 2,
                 'rows': reports, 'provider_calls': 0, 'synthetic_not_task_score': True, 'machine_trusted': 0}
        _save(SMOKE / 'result.json', value)
        return value


def synthetic_input(initial):
    # A new synthetic issue must not inherit real public fixture obligations.
    # This deliberately tests a report hypothesis, not interface-request coverage.
    issue = 'The previous release works without raising.\n'
    return {**initial, 'issue': issue, 'issue_sha256': hashlib.sha256(issue.encode()).hexdigest(),
            'public_fixture_facts': []}


def freeze():
    with configured():
        return base._compiled.freeze()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('smoke', 'freeze'))
    args = parser.parse_args()
    print(json.dumps(asyncio.run(smoke()) if args.command == 'smoke' else freeze(), ensure_ascii=False), flush=True)
