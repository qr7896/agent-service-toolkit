"""Bounded behavioral origins and explicit Boolean-keyword sub-obligations."""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import re

from evals.e1c_blind_boundary import assert_agent_path
from evals.e1c_evaluation_2_api_obligation import obligations, verify_entrypoint
from evals.e1c_evaluation_2_issue_quote_refs import catalogue
from evals.e1c_evaluation_2_qualification import imports
from evals.e1c_evaluation_2_qualification_v3 import git_blob
from evals.e1c_evaluation_2_report_anchor_dev import report_anchors


def boolean_keyword_support(payload, frozen, workspace, candidate, observation):
    claims = [c for c in obligations(frozen['issue']) if c['public_quote'] in payload['expected_quote']]
    if len(claims) != 1:
        return False, ['single_explicit_keyword_request_unproven']
    claim = claims[0]
    if not re.search(r'^\s*' + re.escape(claim['parameter']) + r'\s*:\s*bool(?:\s|,|$)', frozen['issue'], re.M):
        return False, ['public_boolean_parameter_domain_unproven']
    syntax = verify_entrypoint(payload, frozen, workspace)
    entry = next((r for r in syntax['rows'] if r['public_quote'] == claim['public_quote']), None)
    if not entry or entry['status'] != 'explicit_entrypoint_exercised_semantics_unverified':
        return False, ['explicit_API_binding_unproven']
    aliases = imports(ast.parse(payload['setup_source']))
    public_api = claim['api']
    if '.' not in public_api:
        contexts = set(re.findall(r'`([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+\.' + re.escape(claim['owner']) + r')`', frozen['issue']))
        if len(contexts) != 1:
            return False, ['public_qualified_API_context_unproven']
        public_api = contexts.pop()
    names = [name for name, qualified in aliases.items() if qualified == public_api]
    if len(names) != 1:
        return False, ['public_module_not_matched_by_class_name_alone']
    alias = names[0]
    target = ast.parse(payload['target_action'])
    calls = [n for n in ast.walk(target) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == alias]
    if len(calls) != 1 or any(not isinstance(n, (ast.Name, ast.Constant)) for n in [*calls[0].args, *(k.value for k in calls[0].keywords)]):
        return False, ['unique_side_effect_free_constructor_call_unproven']
    requested = [k for k in calls[0].keywords if k.arg == claim['parameter']]
    if len(requested) != 1 or not isinstance(requested[0].value, ast.Constant) or type(requested[0].value.value) is not bool:
        return False, ['requested_boolean_literal_not_exercised']
    reduced = copy.deepcopy(target)
    ctor = next(n for n in ast.walk(reduced) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == alias)
    ctor.keywords = [k for k in ctor.keywords if k.arg != claim['parameter']]
    if ast.dump(reduced, include_attributes=False) != ast.dump(ast.parse(payload['control_action']), include_attributes=False):
        return False, ['normal_differs_beyond_requested_keyword']
    signature = entry['source_signature']
    if signature['requested_parameter_declared'] or signature['has_var_kwargs']:
        return False, ['closed_signature_missing_keyword_unproven']
    path = assert_agent_path(workspace / signature['path'], workspace=workspace)
    raw = path.read_bytes()
    hashes = {r['path']: r['source_sha256'] for r in frozen['windows']}
    if hashes.get(signature['path']) != hashlib.sha256(raw).hexdigest() or raw.replace(b'\r\n', b'\n') != git_blob(workspace, frozen['base_commit'], signature['path']):
        raise ValueError('explicit constructor source not bound to frozen/base identity')
    if hashlib.sha256(candidate['source'].encode()).hexdigest() != candidate['probe_sha256']:
        raise ValueError('original probe source identity differs')
    compiled = ast.parse(candidate['source'])
    probe_calls = [n for n in ast.walk(compiled) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == alias
                   and any(k.arg == claim['parameter'] for k in n.keywords)]
    if len(probe_calls) != 1:
        return False, ['original_probe_constructor_line_unproven']
    if ast.dump(probe_calls[0], include_attributes=False) != ast.dump(calls[0], include_attributes=False):
        return False, ['original_probe_constructor_differs_from_payload']
    matches = [r for r in observation.get('records', []) if r.get('scope') == 'owned_probe'
               and r.get('path') == '/e1c2_model_probe.py' and r.get('line') == probe_calls[0].lineno
               and r.get('exception_type') == 'builtins.TypeError' and r.get('declared_missing_keyword') == claim['parameter']]
    return bool(matches), [] if matches else ['keyword_failure_not_at_original_constructor_line']


def assess(payload, frozen, workspace, candidate, observation, qualification, *, pair=None, documentation=None):
    result = {'schema': 'e1c2-bounded-behavior-gate-v1', 'provider_calls': 0, 'Gold_used': False,
              'sub_obligation_supported': False, 'full_issue_obligations_verified': False,
              'trusted_reproducer': False, 'old_qualification_modified': False}
    if qualification.get('rejected'):
        return {**result, 'status': 'rejected_program_evidence', 'reasons': qualification['rejected']}
    if (observation.get('schema') != 'e1c2-source-bound-exception-observation-v2'
            or observation.get('original_probe_sha256') != candidate['probe_sha256']
            or observation.get('canonical_git_and_effective_file_hash_required') is not True
            or type(observation.get('returncode')) is not int or observation['returncode'] != 1):
        return {**result, 'status': 'rejected_observation_binding', 'reasons': ['original_exception_observation_unbound']}
    if payload.get('oracle') != 'call_completes' or payload.get('assertion') != '':
        return {**result, 'status': 'unknown_oracle_scope', 'reasons': ['non_completion_oracle_outside_v1_scope']}
    spans = catalogue(frozen['issue'])['spans']
    anchors = [a for a in report_anchors(frozen['issue'])['anchors'] if spans[a['quote_ref']]['text'] == payload['expected_quote']]
    if len(anchors) != 1:
        return {**result, 'status': 'unknown_expectation_origin', 'reasons': ['unique_exact_public_anchor_unproven']}
    kind = anchors[0]['kind']
    result.update({'expectation_origin': kind, 'public_change_request_overrides_base_documentation': kind == 'explicit_interface_request'})
    if kind == 'explicit_interface_request':
        if qualification.get('status') != 'mechanism_supported_candidate' or qualification.get('unknown'):
            return {**result, 'status': 'unknown_explicit_request', 'reasons': ['qualified_program_or_mechanism_unproven']}
        supported, reasons = boolean_keyword_support(payload, frozen, workspace, candidate, observation)
        return {**result, 'status': 'supported_boolean_keyword_subobligation' if supported else 'unknown_explicit_request',
                'sub_obligation_supported': supported, 'reasons': reasons,
                'support_scope': 'explicit_boolean_constructor_keyword_acceptance_only',
                'not_covered': ['default_behavior', 'incremental_or_other_functional_behavior', 'other_issue_requests']}
    if kind == 'comparative_report':
        gaps = ['comparison_report_completion_is_hypothesis']
        if not pair or pair.get('shared_keyword_values_match') is not True:
            gaps.append('shared_keyword_values_unproven')
        if not pair or pair.get('all_inputs_match') is not True:
            gaps.append('receiver_or_other_input_state_unproven')
        if documentation and documentation.get('status') == 'documentation_scope_gap':
            gaps.append('observed_input_type_not_explicitly_documented')
        return {**result, 'status': 'conditional_comparative_hypothesis', 'reasons': gaps}
    return {**result, 'status': 'conditional_regression_hypothesis',
            'reasons': ['reported_old_version_behavior_not_verified_normative_oracle', *qualification.get('unknown', [])]}


def audit_dev():
    from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
    from evals.e1c_evaluation_2_issue_input import SOURCE
    from evals.e1c_evaluation_2_issue_quote_refs import resolve

    out = ROOT / '.codex/e1c/evaluation_2/behavior-gate-zero-v1'
    if out.exists():
        raise FileExistsError('behavior audit namespace already started; no replay')
    old = ROOT / '.codex/e1c/evaluation_2/report-anchor-reference-dev-v1'
    private = ROOT / '.codex/e1c/evaluation_2'
    receipts = json.loads((ROOT / 'data/e1c_evaluation_2_authority_integration_results.json').read_bytes())
    qualification_root = private / 'qualification-zero-v3'
    if _sha(qualification_root / 'result.json') != receipts['source_records']['qualification-zero-v3']:
        raise ValueError('qualification cache receipt differs')
    producer = json.loads((ROOT / 'data/e1c_evaluation_2_report_anchor_results.json').read_bytes())
    if _sha(old / 'generation-seal.json') != producer['source_records']['generation-seal.json']:
        raise ValueError('original producer seal changed')
    for name, digest in json.loads((old / 'generation-seal.json').read_bytes())['files'].items():
        if _sha(assert_agent_path(old / name, workspace=old)) != digest:
            raise ValueError('sealed producer artifact changed')
    later = json.loads((ROOT / 'data/e1c_evaluation_2_pair_input_contract_results.json').read_bytes())
    paths = {'pair': private / 'pair-input-observation-zero-v1/result.json', 'documentation': private / 'parameter-contract-zero-v1/result.json'}
    for kind, path in paths.items():
        namespace = path.parent.name
        if _sha(path) != later['source_records'][namespace]['result_sha256']:
            raise ValueError('pair/documentation receipt differs')
    supplements = {kind: {r['instance_id']: r for r in json.loads(path.read_bytes())['rows']} for kind, path in paths.items()}
    _save(out / 'freeze.json', {'provider_calls': 0, 'Gold_read': False, 'original_seal_sha256': _sha(old / 'generation-seal.json'),
                              'sources': {p: _sha(ROOT / p) for p in ['evals/e1c_evaluation_2_behavior_gate.py',
                                  'evals/e1c_evaluation_2_api_obligation.py', 'evals/e1c_evaluation_2_report_anchor_dev.py']},
                              'evidence_sha256': {kind: _sha(path) for kind, path in paths.items()},
                              'qualification_result_sha256': _sha(qualification_root / 'result.json'),
                              'protocol_sha256': _sha(ROOT / 'docs/research/E1C2_BEHAVIOR_GATE_V1_PROTOCOL_2026-10-07.md')})
    selected = {r['instance_id']: r['selected_turn'] for r in json.loads((old / 'state.json').read_bytes())['rows']}
    qrows = {r['instance_id']: r for r in json.loads((qualification_root / 'result.json').read_bytes())['rows']}
    observation_index = private / 'exception-observation-zero-v2/result.json'
    if _sha(observation_index) != producer['zero_records']['exception-observation-zero-v2']:
        raise ValueError('original exception index receipt differs')
    observations = {r['instance_id']: r for r in json.loads(observation_index.read_bytes())['rows']}
    rows = []
    for task in json.loads((old / 'freeze.json').read_bytes())['tasks']:
        iid = task['instance_id']
        turn = old / iid / f"turn-{selected[iid]}"
        frozen = json.loads((turn / 'input.json').read_bytes())
        payload = json.loads(json.loads((turn / 'response.json').read_bytes())['raw'])['probe']
        if 'issue_quote_ref' in payload:
            payload, _ = resolve(payload, frozen['issue'])
        candidate = json.loads((old / iid / 'candidate.json').read_bytes())
        qualification_path = qualification_root / (iid + '.json')
        if _sha(qualification_path) != qrows[iid]['result_sha256']:
            raise ValueError('per-task qualification result changed')
        observation_path = private / 'exception-observation-zero-v2' / iid / 'result.json'
        # Compare to the observation already bound into the published producer receipt.
        if _sha(observation_path) != observations[iid]['observation_sha256']:
            raise ValueError('original exception observation receipt differs')
        result = assess(payload, frozen, SOURCE / iid, candidate, json.loads(observation_path.read_bytes()),
                        json.loads(qualification_path.read_bytes()), **{kind: values.get(iid) for kind, values in supplements.items()})
        _save(out / (iid + '.json'), result)
        rows.append({'instance_id': iid, 'status': result['status'], 'expectation_origin': result.get('expectation_origin'),
                     'sub_obligation_supported': result['sub_obligation_supported'], 'reasons': result.get('reasons', []),
                     'result_sha256': _sha(out / (iid + '.json'))})
    value = {'rows': rows, 'provider_calls': 0, 'provider_tokens': 0, 'Gold_read': False, 'machine_trusted': 0,
             'supported_sub_obligations': sum(r['sub_obligation_supported'] for r in rows),
             'cached_reference_denominator': len(rows), 'fixed_DEV_denominator': 12,
             'full_issue_trust_gate_passed': False, 'live_policy_integrated': False, 'old_scores_or_qualification_changed': False}
    _save(out / 'result.json', value)
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('audit-dev',))
    parser.parse_args()
    print(json.dumps(audit_dev(), ensure_ascii=False), flush=True)
