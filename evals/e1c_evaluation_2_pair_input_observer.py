"""Bounded caller-side input fingerprints for frozen public API contrasts."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from unittest.mock import patch

from evals import e1c_evaluation_2_guard_type_observer as transport

_validate_driver = transport.build_driver
FINGERPRINT = '''import hashlib, json, math
def fingerprint(value, numpy_module=None):
    nodes = [0]
    def visit(v, depth=0):
        nodes[0] += 1
        if depth > 4 or nodes[0] > 64:
            raise ValueError('fingerprint budget')
        cls = type(v)
        if cls is type(None): return ['none']
        if cls is bool: return ['bool', v]
        if cls is int and int.bit_length(v) <= 2048: return ['int', v]
        if cls is float and math.isfinite(v): return ['float', float.hex(v)]
        if cls is str and len(v) <= 8192: return ['str', v]
        if cls is list or cls is tuple:
            if len(v) > 64: raise ValueError('container budget')
            return ['list' if cls is list else 'tuple', [visit(x, depth + 1) for x in v]]
        if cls is dict:
            if len(v) > 64 or any(type(k) is not str or len(k) > 256 for k in v): raise ValueError('mapping budget')
            return ['dict', [[k, visit(v[k], depth + 1)] for k in sorted(v)]]
        if numpy_module is not None and cls is numpy_module.ndarray:
            if v.dtype.kind not in 'biufcSU' or v.nbytes > 65536: raise ValueError('array dtype or budget')
            return ['numpy.ndarray', v.dtype.str, list(v.shape), numpy_module.ndarray.tobytes(v, order='C').hex()]
        raise ValueError('unclassified input')
    try:
        tagged = visit(value)
        raw = json.dumps(tagged, separators=(',', ':'), ensure_ascii=True).encode()
        if len(raw) > 150000: raise ValueError('serialized budget')
        return {'status': 'fingerprinted', 'type': tagged[0], 'sha256': hashlib.sha256(raw).hexdigest()}
    except (ValueError, UnicodeError, RecursionError):
        return {'status': 'unknown', 'type': 'unclassified_or_budget_exceeded', 'sha256': None}
'''
DRIVER = '''import hashlib, json, runpy, subprocess, sys
if hashlib.sha256(open('/e1c2_model_probe.py', 'rb').read()).hexdigest() != DATA['probe_sha256']:
    raise RuntimeError('original model probe changed')
for source in DATA['sites']:
    canonical = subprocess.check_output(['git', '-C', '/testbed', 'show', DATA['base_commit'] + ':' + source['path']])
    live = open('/testbed/' + source['path'], 'rb').read()
    if live != canonical or hashlib.sha256(live).hexdigest() != source['source_sha256']:
        raise RuntimeError('API runtime/canonical source differs')
try:
    import numpy as known_numpy
except ImportError:
    known_numpy = None
records = []
def trace(frame, event, arg):
    if event == 'line' and not records and frame.f_code.co_filename == '/e1c2_model_probe.py' and frame.f_lineno == DATA['call']['line']:
        values = {}
        for name, spec in DATA['call']['parameters'].items():
            present = spec['kind'] == 'literal' or spec['name'] in frame.f_locals
            value = spec['value'] if spec['kind'] == 'literal' else frame.f_locals.get(spec['name'])
            values[name] = dict(fingerprint(value, known_numpy), origin='frozen_literal' if spec['kind'] == 'literal' else 'observed_local') if present else {'status': 'missing', 'sha256': None}
        records.append({'line': DATA['call']['line'], 'api': DATA['call']['api'], 'parameters': values})
    return trace
sys.settrace(trace)
try:
    runpy.run_path('/e1c2_model_probe.py', run_name='__main__')
finally:
    sys.settrace(None)
    print(DATA['marker'] + json.dumps({'schema': 'e1c2-caller-input-observation-v1', 'records': records,
        'argument_values_emitted': False, 'before_call_not_function_body': True, 'API_body_entry_proven': False,
        'public_fixture_value_equivalence_proven': False, 'semantic_alignment_proven': False}))
'''


def call_spec(source, symbol, shared_keywords):
    tree = ast.parse(source)
    imports = {a.asname or a.name: a.name for n in tree.body if isinstance(n, ast.ImportFrom) and n.module and not n.level for a in n.names}
    found = [n.value for n in tree.body if isinstance(n, (ast.Expr, ast.Assign)) and isinstance(n.value, ast.Call)
             and isinstance(n.value.func, ast.Name) and imports.get(n.value.func.id) == symbol]
    if len(found) != 1:
        raise ValueError('unique top-level frozen API call required')
    call = found[0]
    if any(k.arg is None for k in call.keywords) or any(not isinstance(n, (ast.Name, ast.Constant)) for n in [*call.args, *(k.value for k in call.keywords)]):
        raise ValueError('side-effect-free bounded API arguments required')
    params = {k.arg: k.value for k in call.keywords if k.arg in shared_keywords}
    if set(params) != set(shared_keywords) or len(params) > 8:
        raise ValueError('bounded complete shared keyword inventory required')
    params.update({'positional_' + str(i): n for i, n in enumerate(call.args)})
    specs = {}
    for name, node in params.items():
        if isinstance(node, ast.Name) and re.fullmatch(r'[A-Za-z_]\w{0,99}', node.id) and not node.id.startswith('__'):
            specs[name] = {'kind': 'name', 'name': node.id}
        elif isinstance(node, ast.Constant) and type(node.value) in {str, int, float, bool, type(None)}:
            specs[name] = {'kind': 'literal', 'value': node.value}
        else:
            raise ValueError('only frozen literal or local-name parameters supported')
    if not 1 <= len(specs) <= 8:
        raise ValueError('bounded parameter count required')
    return {'line': call.lineno, 'api': symbol, 'parameters': specs}


def build_driver(probe_sha, sites, nonce, spec, base_commit):
    _, marker = _validate_driver(probe_sha, sites, nonce)
    if not re.fullmatch(r'[0-9a-f]{40}', base_commit) or type(spec['line']) is not int or not 1 <= spec['line'] <= 200000:
        raise ValueError('canonical source and frozen call line required')
    if not re.fullmatch(r'[A-Za-z_]\w{0,99}', spec['api']) or not 1 <= len(spec['parameters']) <= 8:
        raise ValueError('bounded API/parameter inventory required')
    for name, parameter in spec['parameters'].items():
        if not re.fullmatch(r'[A-Za-z_]\w{0,99}', name) or parameter['kind'] not in {'name', 'literal'}:
            raise ValueError('invalid parameter specification')
        if parameter['kind'] == 'name' and (set(parameter) != {'kind', 'name'} or not re.fullmatch(r'[A-Za-z_]\w{0,99}', parameter['name']) or parameter['name'].startswith('__')):
            raise ValueError('bounded local name required')
        if parameter['kind'] == 'literal' and (set(parameter) != {'kind', 'value'} or type(parameter['value']) not in {str, int, float, bool, type(None)} or len(json.dumps(parameter['value'])) > 8192):
            raise ValueError('bounded frozen literal required')
    data = {'probe_sha256': probe_sha, 'sites': sites, 'marker': marker, 'call': spec, 'base_commit': base_commit}
    return 'import json\nDATA = json.loads(' + repr(json.dumps(data)) + ')\n' + FINGERPRINT + '\n' + DRIVER, marker


def observe(candidate, probe, sites, spec, image, base_commit, root):
    def builder(probe_sha, selected, nonce):
        return build_driver(probe_sha, selected, nonce, spec, base_commit)

    with patch.object(transport, 'build_driver', builder):
        return transport.observe(candidate, probe, sites, image, base_commit, root)


def compare_inputs(normal, target, shared_keywords):
    if normal.get('returncode') != 0 or target.get('returncode') != 1:
        return {'status': 'unknown_normal_or_target_outcome', 'shared_keyword_values_match': False}
    if len(normal.get('records', [])) != 1 or len(target.get('records', [])) != 1:
        return {'status': 'unknown_missing_or_multiple_snapshots', 'shared_keyword_values_match': False}
    a, b = normal['records'][0]['parameters'], target['records'][0]['parameters']
    rows = []
    for name in sorted(set(a) | set(b)):
        x, y = a.get(name, {}), b.get(name, {})
        supported = x.get('status') == y.get('status') == 'fingerprinted' and bool(x.get('sha256')) and bool(y.get('sha256'))
        rows.append({'parameter': name, 'status': 'same_typed_fingerprint' if supported and x['sha256'] == y['sha256'] else 'different_typed_fingerprint' if supported else 'unknown',
                     'normal_type': x.get('type'), 'target_type': y.get('type')})
    relevant = [r for r in rows if r['parameter'] in shared_keywords]
    matched = len(relevant) == len(shared_keywords) and bool(relevant) and all(r['status'] == 'same_typed_fingerprint' for r in relevant)
    return {'status': 'shared_keywords_supported' if matched else 'unknown_or_different', 'rows': rows,
            'shared_keyword_values_match': matched, 'all_inputs_match': bool(rows) and all(r['status'] == 'same_typed_fingerprint' for r in rows),
            'public_fixture_value_equivalence_proven': False, 'trusted_reproducer': False}


def audit_dev():
    from evals.e1c_blind_boundary import assert_agent_path
    from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
    from evals.e1c_evaluation_2_exception_observer_v2 import project_sites
    from evals.e1c_evaluation_2_expectation_dev import contrast_binding
    from evals.e1c_evaluation_2_issue_input import SOURCE
    from evals.e1c_evaluation_2_issue_quote_refs import resolve

    old = ROOT / '.codex/e1c/evaluation_2/report-anchor-reference-dev-v1'
    out = ROOT / '.codex/e1c/evaluation_2/pair-input-observation-zero-v1'
    if out.exists():
        raise FileExistsError('pair observation namespace already started; no retry')
    if _sha(old / 'generation-seal.json') != '5997675327f8f246b179413f0c2df5efd2b66fd2edacc2f6db430796588ea86f':
        raise ValueError('original producer seal differs')
    for name, digest in json.loads((old / 'generation-seal.json').read_bytes())['files'].items():
        if _sha(assert_agent_path(old / name, workspace=old)) != digest:
            raise ValueError('sealed producer file changed')
    frame = json.loads((old / 'freeze.json').read_bytes())
    selected = {r['instance_id']: r['selected_turn'] for r in json.loads((old / 'state.json').read_bytes())['rows']}
    _save(out / 'freeze.json', {'provider_calls': 0, 'Gold_read': False, 'original_seal_sha256': _sha(old / 'generation-seal.json'),
                              'module_sha256': _sha(Path(__file__)),
                              'protocol_sha256': _sha(ROOT / 'docs/research/E1C2_PAIR_INPUT_OBSERVER_V1_PROTOCOL_2026-10-07.md')})
    rows = []
    for task in frame['tasks']:
        iid = task['instance_id']
        turn = old / iid / f'turn-{selected[iid]}'
        frozen = json.loads((turn / 'input.json').read_bytes())
        payload = json.loads(json.loads((turn / 'response.json').read_bytes())['raw'])['probe']
        if 'issue_quote_ref' in payload:
            payload, _ = resolve(payload, frozen['issue'])
        binding = contrast_binding(payload, frozen, SOURCE / iid)
        if binding['status'] == 'not_applicable':
            rows.append({'instance_id': iid, 'status': 'not_applicable_no_public_API_pair'})
            continue
        if binding['status'] != 'explicit_contrast_exercised_syntactically':
            rows.append({'instance_id': iid, 'status': 'unknown_static_pair'})
            continue
        results = []
        for index, role in enumerate(('normal', 'target')):
            path = turn / 'control_candidate.json' if role == 'normal' else old / iid / 'candidate.json'
            candidate = json.loads(path.read_bytes())
            probe = turn / 'control-1' / (candidate['probe_sha256'] + '.py') if role == 'normal' else old / iid / 'execution' / (candidate['probe_sha256'] + '.py')
            api = binding['source_bindings'][index]
            spec = call_spec(candidate['source'], api['symbol'], binding['shared_keywords'])
            sites, proofs = project_sites(SOURCE / iid, [{'path': api['path'], 'line': api['line'], 'variable': binding['shared_keywords'][0],
                                                        'source_sha256': api['source_sha256']}])
            try:
                result = observe(candidate, probe, sites, spec, task['image_id'], frozen['base_commit'], out / iid / role)
            except Exception as exc:
                _save(out / 'failure.json', {'instance_id': iid, 'role': role, 'error_type': type(exc).__name__, 'provider_calls': 0, 'no_retry': True})
                raise
            _save(out / iid / (role + '-projection.json'), {'proofs': proofs, 'probe_sha256': candidate['probe_sha256'], 'call_spec': spec})
            results.append(result)
        comparison = compare_inputs(*results, binding['shared_keywords'])
        rows.append({'instance_id': iid, **comparison, 'normal_returncode': results[0]['returncode'], 'target_returncode': results[1]['returncode'],
                     'normal_result_sha256': _sha(out / iid / 'normal/result.json'), 'target_result_sha256': _sha(out / iid / 'target/result.json')})
    value = {'rows': rows, 'cached_reference_denominator': len(rows), 'fixed_DEV_denominator': 12,
             'provider_calls': 0, 'provider_tokens': 0, 'Gold_read': False, 'machine_trusted': 0,
             'old_scores_or_qualification_changed': False, 'new_model_generation': False, 'API_body_entry_proven': False}
    _save(out / 'result.json', value)
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('audit-dev',))
    parser.parse_args()
    print(json.dumps(audit_dev(), ensure_ascii=False), flush=True)
