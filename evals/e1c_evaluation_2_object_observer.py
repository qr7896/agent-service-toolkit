"""Values-free constructor binding observation, not semantic attestation."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path
from unittest.mock import patch

from evals import e1c_evaluation_2_guard_type_observer as transport
from evals.e1c_blind_boundary import assert_agent_path
from evals.e1c_strict_v5_boundary import assert_production_relative_path

_validate_driver, _docker_command = transport.build_driver, transport.docker_command
DRIVER = '''import hashlib, json, runpy, subprocess, sys
if hashlib.sha256(open('/e1c2_model_probe.py', 'rb').read()).hexdigest() != DATA['probe_sha256']:
    raise RuntimeError('original model probe changed')
for source in DATA['export_sources']:
    canonical = subprocess.check_output(['git', '-C', '/testbed', 'show', DATA['base_commit'] + ':' + source['path']])
    live = open('/testbed/' + source['path'], 'rb').read()
    if hashlib.sha256(canonical).hexdigest() != source['source_sha256'] or live != canonical:
        raise RuntimeError('export chain runtime/base identity differs')
records = []
seen = set()
mro_descriptor = type.__dict__['__mro__']
def trace(frame, event, arg):
    if event == 'call':
        for binding in DATA['bindings']:
            key = (binding['path'], binding['line'], binding['symbol'])
            code = frame.f_code
            if key not in seen and code.co_filename == '/testbed/' + binding['path'] and code.co_firstlineno == binding['line'] and code.co_name == '__init__':
                seen.add(key)
                present = 'self' in frame.f_locals
                declared = frame.f_globals.get(binding['symbol'])
                real_class = isinstance(declared, type)
                cls = type(frame.f_locals['self']) if present else None
                mro = mro_descriptor.__get__(cls, type) if present else ()
                records.append({'path': binding['path'], 'line': binding['line'], 'symbol': binding['symbol'],
                    'self_present': present, 'declared_class_present': real_class,
                    'instance_type_is_declared_class': bool(real_class and cls is declared),
                    'declared_class_in_instance_mro': bool(real_class and any(c is declared for c in mro))})
    return trace
sys.settrace(trace)
try:
    runpy.run_path('/e1c2_model_probe.py', run_name='__main__')
finally:
    sys.settrace(None)
    print(DATA['marker'] + json.dumps({'schema': 'e1c2-constructor-object-observation-v1', 'records': records,
        'argument_values_emitted': False, 'object_attributes_or_repr_emitted': False,
        'runtime_export_sources_checked': True, 'semantic_alignment_proven': False}))
'''


def constructor_bindings(rows, workspace):
    bindings, sources, unknown = [], {}, []
    for row in rows:
        if row['status'] != 'static_chain_supported':
            unknown.append('static_export_chain_unknown')
            continue
        for source in row['chain']:
            name = assert_production_relative_path(source['path'])
            raw = assert_agent_path(workspace / name, workspace=workspace).read_bytes()
            if hashlib.sha256(raw).hexdigest() != source['host_sha256']:
                raise ValueError('export source changed before observation')
            effective = hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()
            if effective != source['canonical_sha256']:
                raise ValueError('export LF/canonical identity differs')
            if name in sources and sources[name]['source_sha256'] != effective:
                raise ValueError('conflicting export source identity')
            sources[name] = {'path': name, 'source_sha256': effective}
        terminal = row['chain'][-1]
        symbol = terminal['qualified'].rsplit('.', 1)[-1]
        tree = ast.parse(assert_agent_path(workspace / terminal['path'], workspace=workspace).read_bytes())
        classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == symbol]
        methods = [n for c in classes for n in c.body if isinstance(n, ast.FunctionDef) and n.name == '__init__']
        if len(classes) != 1 or len(methods) != 1 or methods[0].decorator_list or not methods[0].args.args or methods[0].args.args[0].arg != 'self':
            unknown.append('direct_plain_constructor_unproven')
            continue
        binding = {'path': terminal['path'], 'line': methods[0].lineno, 'symbol': symbol}
        if binding not in bindings:
            bindings.append(binding)
    return bindings, list(sources.values()), sorted(set(unknown))


def build_driver(probe_sha, sites, nonce, bindings, export_sources, base_commit):
    _, marker = _validate_driver(probe_sha, sites, nonce)
    if not re.fullmatch(r'[0-9a-f]{40}', base_commit) or not 1 <= len(bindings) <= 2 or not 1 <= len(export_sources) <= 8:
        raise ValueError('bounded canonical object observation required')
    for b in bindings:
        if set(b) != {'path', 'line', 'symbol'} or not re.fullmatch(r'[A-Za-z_]\w{0,99}', b['symbol']) or b['symbol'].startswith('__'):
            raise ValueError('bounded class symbol required')
        if not any(s['path'] == b['path'] and s['line'] == b['line'] and s['variable'] == 'self' for s in sites):
            raise ValueError('binding must match validated constructor site')
    for source in export_sources:
        assert_production_relative_path(source['path'])
        if set(source) != {'path', 'source_sha256'} or not re.fullmatch(r'[0-9a-f]{64}', source['source_sha256']):
            raise ValueError('bounded export source identity required')
    if len({s['path'] for s in export_sources}) != len(export_sources):
        raise ValueError('duplicate export source identity')
    if any(not any(s['path'] == site['path'] and s['source_sha256'] == site['source_sha256'] for s in export_sources) for site in sites):
        raise ValueError('constructor source not in export identity chain')
    data = {'probe_sha256': probe_sha, 'marker': marker, 'bindings': bindings, 'export_sources': export_sources, 'base_commit': base_commit}
    return 'import json\nDATA = json.loads(' + repr(json.dumps(data)) + ')\n' + DRIVER, marker


def observe(candidate, probe, bindings, export_sources, image, base_commit, root, *, blocked_import_dir=None):
    sites = [{'path': b['path'], 'line': b['line'], 'variable': 'self',
              'source_sha256': next(s['source_sha256'] for s in export_sources if s['path'] == b['path'])} for b in bindings]

    def builder(probe_sha, selected, nonce):
        return build_driver(probe_sha, selected, nonce, bindings, export_sources, base_commit)

    def command(descriptor, selected_image, commit, mounted):
        return _docker_command(descriptor, selected_image, commit, mounted, blocked_import_dir=blocked_import_dir)

    with patch.object(transport, 'build_driver', builder), patch.object(transport, 'docker_command', command):
        return transport.observe(candidate, probe, sites, image, base_commit, root)


def audit_dev():
    from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
    from evals.e1c_evaluation_2_issue_input import SOURCE

    old = ROOT / '.codex/e1c/evaluation_2/report-anchor-reference-dev-v1'
    chains = ROOT / '.codex/e1c/evaluation_2/export-chain-zero-v1/result.json'
    public_receipt = ROOT / 'data/e1c_evaluation_2_reference_scope_results.json'
    out = ROOT / '.codex/e1c/evaluation_2/object-observation-zero-v1'
    if out.exists():
        raise FileExistsError('object observation namespace already started; no retry')
    expected = json.loads(public_receipt.read_bytes())['source_records']['export-chain-zero-v1']['result_sha256']
    if _sha(chains) != expected or _sha(old / 'generation-seal.json') != '5997675327f8f246b179413f0c2df5efd2b66fd2edacc2f6db430796588ea86f':
        raise ValueError('original producer/export chain receipt changed')
    for path, digest in json.loads((old / 'generation-seal.json').read_bytes())['files'].items():
        if _sha(assert_agent_path(old / path, workspace=old)) != digest:
            raise ValueError('sealed original producer artifact changed')
    frame = json.loads((old / 'freeze.json').read_bytes())
    all_chains = json.loads(chains.read_bytes())['rows']
    selected = {r['instance_id']: r['selected_turn'] for r in json.loads((old / 'state.json').read_bytes())['rows']}
    _save(out / 'freeze.json', {'provider_calls': 0, 'Gold_read': False, 'original_seal_sha256': _sha(old / 'generation-seal.json'),
                              'export_chain_sha256': _sha(chains), 'module_sha256': _sha(Path(__file__)),
                              'protocol_sha256': _sha(ROOT / 'docs/research/E1C2_OBJECT_OBSERVER_V1_PROTOCOL_2026-10-07.md')})
    rows = []
    for task in frame['tasks']:
        iid = task['instance_id']
        relevant = [r for r in all_chains if r['instance_id'] == iid]
        if not relevant:
            rows.append({'instance_id': iid, 'status': 'not_applicable_no_conditional_binding'})
            continue
        bindings, exports, unknown = constructor_bindings(relevant, SOURCE / iid)
        if unknown or not bindings:
            rows.append({'instance_id': iid, 'status': 'unknown_constructor', 'unknown': unknown})
            continue
        candidate = json.loads((old / iid / 'candidate.json').read_bytes())
        probe = old / iid / 'execution' / (candidate['probe_sha256'] + '.py')
        frozen = json.loads((old / iid / f'turn-{selected[iid]}' / 'input.json').read_bytes())
        missing = task['environment']['missing_optional_import']
        blocker = old / iid / 'execution/optional_missing' if missing else None
        if missing and (blocker / (missing + '.py')).read_bytes() != f"raise ModuleNotFoundError(\"No module named '{missing}'\")\n".encode():
            raise ValueError('original dependency blocker differs')
        try:
            result = observe(candidate, probe, bindings, exports, task['image_id'], frozen['base_commit'], out / iid,
                             blocked_import_dir=blocker)
        except Exception as exc:
            _save(out / 'failure.json', {'instance_id': iid, 'status': 'blocked_observation', 'error_type': type(exc).__name__,
                                        'provider_calls': 0, 'Gold_read': False, 'no_retry': True})
            raise
        observed = result['records']
        aligned = len(observed) == len(bindings) and all(r['declared_class_in_instance_mro'] for r in observed)
        rows.append({'instance_id': iid, 'status': 'constructor_binding_observed' if aligned else 'unknown_runtime_binding',
                     'records': observed, 'returncode': result['returncode'], 'result_sha256': _sha(out / iid / 'result.json'),
                     'bindings_expected': len(bindings), 'runtime_binding_aligned': aligned})
    value = {'rows': rows, 'cached_reference_denominator': len(frame['tasks']), 'fixed_DEV_denominator': 12,
             'provider_calls': 0, 'provider_tokens': 0, 'Gold_read': False, 'machine_trusted': 0,
             'original_scores_or_qualification_changed': False, 'new_model_generation': False,
             'semantic_alignment_proven': False, 'instrumented_same_semantics_claimed': False}
    _save(out / 'result.json', value)
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('audit-dev',))
    parser.parse_args()
    print(json.dumps(audit_dev(), ensure_ascii=False), flush=True)
