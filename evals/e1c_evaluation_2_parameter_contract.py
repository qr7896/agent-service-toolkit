"""NumPy-style parameter declarations only; never doc examples or test oracles."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

from evals.e1c_blind_boundary import assert_agent_path
from evals.e1c_evaluation_2_qualification_v3 import git_blob


def parameter_declarations(node, requested):
    doc = ast.get_docstring(node, clean=False)
    if not doc or not node.body or len(requested) > 8:
        return []
    lines = doc.splitlines()
    active, declarations = False, []
    for index, line in enumerate(lines):
        text = line.strip()
        heading = index + 1 < len(lines) and re.fullmatch(r'-{3,}', lines[index + 1].strip())
        if heading:
            active = text == 'Parameters'
            continue
        if not active:
            continue
        match = re.fullmatch(r'([A-Za-z_]\w*)\s*:\s*(.{1,256})', text)
        if match and match[1] in requested:
            declarations.append({'parameter': match[1], 'declaration': match[2],
                                 'source_line': node.body[0].lineno + index, 'origin': 'production_parameter_doc'})
    return declarations


def compare_documented_type(declaration, observed_type):
    text = declaration.split(', default')[0].strip().lower()
    # This is positive support vocabulary, not a universal rejection rule.
    if text == 'list of str':
        return 'documented_container_kind_supported_elements_unproven' if observed_type == 'list' else 'observed_type_not_explicitly_documented'
    if text in {'int', 'float', 'bool', 'str'}:
        return 'documented_type_supported' if observed_type == text else 'observed_type_not_explicitly_documented'
    return 'unknown_documentation_grammar'


def audit_dev():
    from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
    from evals.e1c_evaluation_2_issue_input import SOURCE

    pair = ROOT / '.codex/e1c/evaluation_2/pair-input-observation-zero-v1'
    source = ROOT / '.codex/e1c/evaluation_2/report-anchor-reference-dev-v1'
    out = ROOT / '.codex/e1c/evaluation_2/parameter-contract-zero-v1'
    if out.exists():
        raise FileExistsError('parameter contract audit already started; no replay')
    # Bind the observation result to its recorded freeze and original producer.
    freeze = json.loads((pair / 'freeze.json').read_bytes())
    if _sha(source / 'generation-seal.json') != freeze['original_seal_sha256']:
        raise ValueError('original producer seal changed')
    for name, digest in json.loads((source / 'generation-seal.json').read_bytes())['files'].items():
        if _sha(assert_agent_path(source / name, workspace=source)) != digest:
            raise ValueError('sealed producer artifact changed')
    selected = {r['instance_id']: r['selected_turn'] for r in json.loads((source / 'state.json').read_bytes())['rows']}
    pair_result = json.loads((pair / 'result.json').read_bytes())
    _save(out / 'freeze.json', {'module_sha256': _sha(Path(__file__)), 'pair_result_sha256': _sha(pair / 'result.json'),
                              'protocol_sha256': _sha(ROOT / 'docs/research/E1C2_PARAMETER_CONTRACT_V1_PROTOCOL_2026-10-07.md'),
                              'provider_calls': 0, 'Gold_read': False})
    rows = []
    for row in pair_result['rows']:
        iid = row['instance_id']
        if row['status'] == 'not_applicable_no_public_API_pair':
            rows.append({'instance_id': iid, 'status': 'not_applicable'})
            continue
        turn = source / iid / f"turn-{selected[iid]}"
        frozen = json.loads((turn / 'input.json').read_bytes())
        binding = json.loads((turn / 'expectation-binding.json').read_bytes())['contrast']
        observed = {r['parameter']: r for r in row.get('rows', [])}
        findings = []
        for role, api in zip(('normal', 'target'), binding['source_bindings'], strict=True):
            path = assert_agent_path(SOURCE / iid / api['path'], workspace=SOURCE / iid)
            raw = path.read_bytes()
            if _sha(path) != api['source_sha256'] or raw.replace(b'\r\n', b'\n') != git_blob(SOURCE / iid, frozen['base_commit'], api['path']):
                raise ValueError('parameter contract source differs from original base')
            node = next(n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name == api['symbol'])
            for item in parameter_declarations(node, binding['shared_keywords']):
                tag = observed.get(item['parameter'], {}).get(role + '_type')
                findings.append({**item, 'role': role, 'api': api['symbol'], 'path': api['path'], 'source_sha256': _sha(path),
                                 'observed_type': tag, 'status': compare_documented_type(item['declaration'], tag)})
        rows.append({'instance_id': iid, 'status': 'documentation_scope_gap' if any(
            r['status'] == 'observed_type_not_explicitly_documented' for r in findings) else 'bounded_documentation_audited',
            'findings': findings, 'source_docs_are_not_universal_truth': True, 'explicit_public_change_request_may_override_base_docs': True,
            'public_report_completion_is_still_hypothesis': True, 'trusted_reproducer': False})
    value = {'rows': rows, 'provider_calls': 0, 'provider_tokens': 0, 'Gold_read': False, 'machine_trusted': 0,
             'cached_reference_denominator': len(rows), 'old_scores_or_qualification_changed': False, 'model_inputs_modified': False}
    _save(out / 'result.json', value)
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('audit-dev',))
    parser.parse_args()
    print(json.dumps(audit_dev(), ensure_ascii=False), flush=True)
