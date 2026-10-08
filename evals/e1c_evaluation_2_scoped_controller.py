"""Fresh scope gate: exact definition headers and unknown-preserving DEV selection."""

from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import json
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from evals import e1c_evaluation_2_qualified_controller as base
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

OUT = ROOT / '.codex/e1c/evaluation_2/scoped-controller-dev-v1'
SMOKE = ROOT / '.codex/e1c/evaluation_2/scoped-controller-zero-smoke-v1'
FAILURE = ROOT / '.codex/e1c/evaluation_2/scoped-controller-failure-smoke-v1'
AUDIT = ROOT / '.codex/e1c/evaluation_2/scoped-controller-cache-audit-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_SCOPED_CONTROLLER_PROTOCOL_2026-10-08.md'
MODULES = (*base.MODULES, 'evals/e1c_evaluation_2_scoped_controller.py')
_execute, _preflight = base.execute_probe, base.preflight


def source_contracts(frozen, workspace):
    records, trees = [], {}
    for row in frozen['windows']:
        name = base.assert_production_relative_path(row['path'])
        file = base.assert_agent_path(workspace / name, workspace=workspace)
        if file.stat().st_size > 1_000_000:
            raise ValueError('bounded production source required')
        raw = file.read_bytes()
        if hashlib.sha256(raw).hexdigest() != row['source_sha256'] or raw.replace(b'\r\n', b'\n') != base.git_blob(workspace, frozen['base_commit'], name):
            raise ValueError('scoped Controller source identity differs')
        if name not in trees:
            tree = ast.parse(raw)
            entries = [(n, None) for n in tree.body if isinstance(n, ast.FunctionDef)]
            entries += [(n, c.name) for c in tree.body if isinstance(c, ast.ClassDef) for n in c.body if isinstance(n, ast.FunctionDef)]
            trees[name] = entries
        candidates = [(n, owner) for n, owner in trees[name] if n.name == row.get('symbol')]
        if not candidates:
            continue  # Class/guard windows are not function-parameter certificates.
        matching = [(n, owner) for n, owner in candidates if type(row.get('start_line')) is int and n.lineno == row['start_line']
                    and (not row.get('owner') or owner == row['owner'])]
        item = {'path': name, 'source_sha256': row['source_sha256'], 'symbol': row['symbol'], 'declarations': [],
                'relation_type': 'parameter_contract', 'origin': 'frozen_production_definition', 'depth': 0,
                'does_not_override_explicit_public_change_request': True, 'target_API_binding_proven': False}
        if len(matching) != 1:
            item.update({'binding_status': 'unknown_definition_scope', 'owner': row.get('owner'),
                         'reason': 'unique_exact_header_and_owner_unproven'})
        else:
            node, owner = matching[0]
            parameters = [a.arg for a in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs) if a.arg not in {'self', 'cls'}][:8]
            item.update({'binding_status': 'unique_definition_header', 'owner': owner, 'definition_line': node.lineno,
                         'declarations': base.parameter_declarations(node, parameters)})
        if item not in records:
            records.append(item)
    base.audit_repair_visible_payload(records)
    return records[:8]


def action_gate(verdict):
    q, behavior = verdict.get('qualification', {}), verdict.get('behavior', {})
    rejected = list(q.get('rejected', []))
    missing = list(q.get('unknown', []))
    if verdict.get('trusted_reproducer') is True or behavior.get('trusted_reproducer') is True:
        rejected.append('full_issue_trust_outside_scoped_method')
    if q.get('status') == 'rejected' or behavior.get('status', '').startswith('rejected'):
        rejected.append('rejected_qualification_or_behavior')
    if q.get('status') not in {'mechanism_supported_candidate', 'behavior_candidate_mechanism_unproven'}:
        missing.append('supported_program_qualification_unproven')
    bstatus = behavior.get('status')
    if bstatus == 'supported_boolean_keyword_subobligation' and behavior.get('sub_obligation_supported') is True:
        scope, remaining = 'sub_obligation_only', ['remaining_issue_obligations_not_verified']
    elif bstatus in {'conditional_comparative_hypothesis', 'conditional_regression_hypothesis'}:
        scope, remaining = 'conditional_completion_hypothesis', behavior.get('reasons', [])
    else:
        scope, remaining = 'unknown', behavior.get('reasons', [])
        missing.append('behavior_scope_unproven')
    action = 'REJECT' if rejected else 'ACQUIRE_EVIDENCE_OR_ABSTAIN' if missing else 'INDEPENDENT_DEV_GRADE_ONLY'
    requests = [{'retrieve': row['symbol']} for row in q.get('program_evidence', {}).get('unexposed_dependency_bindings', [])
                if isinstance(row.get('symbol'), str) and row['symbol'].isidentifier()][:2]
    return {'schema': 'e1c2-scoped-action-gate-v1', 'action': action, 'scope': scope,
            'rejected': sorted(set(rejected)), 'missing_evidence': sorted(set(missing)),
            'remaining_behavior_obligations': sorted(set(remaining)), 'bounded_source_requests': requests,
            'DEV_candidate_eligible': action == 'INDEPENDENT_DEV_GRADE_ONLY', 'repair_eligible': False,
            'full_issue_trusted': False, 'canary_ready': False}


def execute_probe(payload, frozen, workspace, image, root, environment, locked=None):
    feedback, oracle, candidate, execution = _execute(payload, frozen, workspace, image, root, environment, locked)
    if candidate is None:
        return feedback, oracle, candidate, execution
    gate = action_gate(feedback['controller_verdict'])
    _save(root / 'controller-scope-gate.json', gate)
    feedback = {**feedback, 'scope_gate': gate}
    if not gate['DEV_candidate_eligible']:
        # Keep per-turn raw candidate/execution; only stop premature terminal selection.
        feedback['status'] = 'action_rejected' if gate['action'] == 'REJECT' else 'evidence_required_before_selection'
        return feedback, oracle, None, execution
    return feedback, oracle, candidate, execution


def preflight():
    return {**_preflight(), 'schema': 'e1c2-scoped-controller-four-reference-dev-v1',
            'unique_definition_header_scope': True, 'unknown_blocks_terminal_DEV_selection': True,
            'partial_or_hypothesis_never_repair_eligible': True, 'real_provider_run_enabled': False}


@contextmanager
def configured():
    with ExitStack() as stack:
        for key, value in [('OUT', OUT), ('SMOKE', SMOKE), ('PROTOCOL', PROTOCOL), ('MODULES', MODULES),
                           ('source_contracts', source_contracts), ('execute_probe', execute_probe), ('preflight', preflight)]:
            stack.enter_context(patch.object(base, key, value))
        stack.enter_context(base.configured())
        yield


def audit_dev():
    if AUDIT.exists():
        raise FileExistsError('scope cache audit already started; no retry')
    qualified = json.loads((ROOT / 'data/e1c_evaluation_2_authority_integration_results.json').read_bytes())['rows']
    behavioral = json.loads((ROOT / 'data/e1c_evaluation_2_behavior_version_results.json').read_bytes())['behavior_result']['rows']
    if len(qualified) != 4 or {r['instance_id'] for r in qualified} != {r['instance_id'] for r in behavioral}:
        raise ValueError('complete four-reference cached evidence required')
    pairs = []
    for row in qualified:
        iid = row['instance_id']
        qfile = ROOT / f'.codex/e1c/evaluation_2/qualification-zero-v3/{iid}.json'
        bfile = ROOT / f'.codex/e1c/evaluation_2/behavior-gate-zero-v1/{iid}.json'
        b = next(r for r in behavioral if r['instance_id'] == iid)
        if _sha(qfile) != row['result_sha256'] or _sha(bfile) != b['result_sha256']:
            raise ValueError('cached qualification/behavior identity differs')
        pairs.append((iid, qfile, bfile))
    _save(AUDIT / 'freeze.json', {'module_sha256': _sha(ROOT / 'evals/e1c_evaluation_2_scoped_controller.py'),
                                'protocol_sha256': _sha(PROTOCOL), 'provider_calls': 0,
                                'cached_files': {str(p.relative_to(ROOT)): _sha(p) for _, q, b in pairs for p in (q, b)}})
    rows = []
    for iid, q, b in pairs:
        gate = action_gate({'qualification': json.loads(q.read_bytes()), 'behavior': json.loads(b.read_bytes()), 'trusted_reproducer': False})
        rows.append({'instance_id': iid, **gate})
    value = {'rows': rows, 'provider_calls': 0, 'provider_tokens': 0, 'Gold_read': False, 'new_containers': 0,
             'cached_reference_denominator': 4, 'fixed_DEV_denominator': 12, 'machine_trusted': 0,
             'old_scores_or_qualification_changed': False, 'shadow_audit_not_new_generation': True}
    _save(AUDIT / 'result.json', value)
    return value


async def failure_smoke():
    from evals import e1c_evaluation_2_controller_failure_smoke as driver
    with configured(), patch.object(driver, 'OUT', FAILURE), patch.object(driver, 'PROTOCOL', PROTOCOL):
        value = await driver.run()
        gate = json.loads((FAILURE / 'fixture/turn-2/controller-scope-gate.json').read_bytes())
        if gate['action'] != 'INDEPENDENT_DEV_GRADE_ONLY' or gate['repair_eligible']:
            raise ValueError('synthetic scope gate did not restrict candidate')
        _save(FAILURE / 'scope-result.json', {'scope_gate': gate, 'provider_calls': 0, 'synthetic_not_task_score': True})
        return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('smoke', 'freeze', 'failure-smoke', 'audit-dev'))
    args = parser.parse_args()
    if args.command == 'failure-smoke':
        value = asyncio.run(failure_smoke())
    elif args.command == 'audit-dev':
        value = audit_dev()
    else:
        with configured():
            value = asyncio.run(base.smoke()) if args.command == 'smoke' else base.freeze()
    print(json.dumps(value, ensure_ascii=False), flush=True)
