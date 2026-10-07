"""Module-bound runtime constructor relationships, without guessing inheritance."""

from __future__ import annotations

import argparse
import ast
import json
from unittest.mock import patch

from evals import e1c_evaluation_2_object_observer as base
from evals.e1c_blind_boundary import assert_agent_path

_strict_driver = base.build_driver
DRIVER = base.DRIVER.replace(
    "key = (binding['path'], binding['line'], binding['symbol'])",
    "key = (binding['path'], frame.f_code.co_firstlineno, binding['symbol'])",
).replace("code.co_firstlineno == binding['line']", "code.co_firstlineno in binding['constructor_lines']").replace(
    "'line': binding['line'], 'symbol': binding['symbol']",
    "'line': code.co_firstlineno, 'declared_class_line': binding['line'], 'symbol': binding['symbol']",
).replace("'e1c2-constructor-object-observation-v1'", "'e1c2-constructor-object-observation-v2'")


def constructor_bindings(rows, workspace):
    _, sources, _ = base.constructor_bindings(rows, workspace)  # Keep all source identity checks.
    bindings, unknown = [], []
    for row in rows:
        if row['status'] != 'static_chain_supported':
            unknown.append('static_chain_unknown')
            continue
        terminal = row['chain'][-1]
        symbol = terminal['qualified'].rsplit('.', 1)[-1]
        tree = ast.parse(assert_agent_path(workspace / terminal['path'], workspace=workspace).read_bytes())
        declared = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == symbol]
        lines = sorted({n.lineno for c in tree.body if isinstance(c, ast.ClassDef) for n in c.body
                        if isinstance(n, ast.FunctionDef) and n.name == '__init__' and not n.decorator_list
                        and n.args.args and n.args.args[0].arg == 'self'})
        if len(declared) != 1 or not 1 <= len(lines) <= 32:
            unknown.append('bounded_module_constructor_inventory_unknown')
            continue
        value = {'path': terminal['path'], 'symbol': symbol, 'line': declared[0].lineno, 'constructor_lines': lines}
        if value not in bindings:
            bindings.append(value)
    return bindings, sources, unknown


def build_driver(probe_sha, sites, nonce, bindings, export_sources, base_commit):
    plain = [{k: b[k] for k in ('path', 'line', 'symbol')} for b in bindings]
    _, marker = _strict_driver(probe_sha, sites, nonce, plain, export_sources, base_commit)
    for binding in bindings:
        lines = binding['constructor_lines']
        if set(binding) != {'path', 'line', 'symbol', 'constructor_lines'} or not 1 <= len(lines) <= 32 or any(
            type(n) is not int or not 1 <= n <= 200000 for n in lines
        ):
            raise ValueError('bounded source-derived constructor inventory required')
    data = {'probe_sha256': probe_sha, 'marker': marker, 'bindings': bindings,
            'export_sources': export_sources, 'base_commit': base_commit}
    return 'import json\nDATA = json.loads(' + repr(json.dumps(data)) + ')\n' + DRIVER, marker


def observe(*args, **kwargs):
    with patch.object(base, 'build_driver', build_driver):
        return base.observe(*args, **kwargs)


def audit_dev():
    from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
    from evals.e1c_evaluation_2_issue_input import SOURCE

    out = ROOT / '.codex/e1c/evaluation_2/object-observation-zero-v2'
    if out.exists():
        raise FileExistsError('object v2 namespace already started; no retry')
    old = ROOT / '.codex/e1c/evaluation_2/report-anchor-reference-dev-v1'
    chains = ROOT / '.codex/e1c/evaluation_2/export-chain-zero-v1/result.json'
    expected = json.loads((ROOT / 'data/e1c_evaluation_2_reference_scope_results.json').read_bytes())['source_records']['export-chain-zero-v1']['result_sha256']
    if _sha(chains) != expected or _sha(old / 'generation-seal.json') != '5997675327f8f246b179413f0c2df5efd2b66fd2edacc2f6db430796588ea86f':
        raise ValueError('original seal/export receipt changed')
    for path, digest in json.loads((old / 'generation-seal.json').read_bytes())['files'].items():
        if _sha(assert_agent_path(old / path, workspace=old)) != digest:
            raise ValueError('original producer artifact changed')
    tasks = json.loads((old / 'freeze.json').read_bytes())['tasks']
    selected = {r['instance_id']: r['selected_turn'] for r in json.loads((old / 'state.json').read_bytes())['rows']}
    _save(out / 'freeze.json', {'provider_calls': 0, 'Gold_read': False, 'export_result_sha256': _sha(chains),
                              'v1_results_sha256': _sha(ROOT / '.codex/e1c/evaluation_2/object-observation-zero-v1/result.json'),
                              'modules': {p: _sha(ROOT / p) for p in ['evals/e1c_evaluation_2_object_observer.py', 'evals/e1c_evaluation_2_object_observer_v2.py']},
                              'protocol_sha256': _sha(ROOT / 'docs/research/E1C2_OBJECT_OBSERVER_V2_PROTOCOL_2026-10-07.md')})
    chain_rows = json.loads(chains.read_bytes())['rows']
    rows = []
    for task in tasks:
        iid = task['instance_id']
        relevant = [r for r in chain_rows if r['instance_id'] == iid]
        if not relevant:
            rows.append({'instance_id': iid, 'status': 'not_applicable_no_conditional_binding'})
            continue
        bindings, sources, unknown = constructor_bindings(relevant, SOURCE / iid)
        if unknown:
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
            result = observe(candidate, probe, bindings, sources, task['image_id'], frozen['base_commit'], out / iid,
                             blocked_import_dir=blocker)
        except Exception as exc:
            _save(out / 'failure.json', {'instance_id': iid, 'error_type': type(exc).__name__, 'provider_calls': 0, 'no_retry': True})
            raise
        coverage = [{'path': b['path'], 'symbol': b['symbol'], 'relationship_observed': any(
            r['path'] == b['path'] and r['symbol'] == b['symbol'] and r['declared_class_in_instance_mro']
            for r in result['records'])} for b in bindings]
        rows.append({'instance_id': iid, 'status': 'constructor_relationships_observed' if all(c['relationship_observed'] for c in coverage) else 'unknown_runtime_binding',
                     'coverage': coverage, 'records': result['records'], 'returncode': result['returncode'],
                     'result_sha256': _sha(out / iid / 'result.json')})
    value = {'rows': rows, 'cached_reference_denominator': len(tasks), 'fixed_DEV_denominator': 12,
             'provider_calls': 0, 'provider_tokens': 0, 'Gold_read': False, 'machine_trusted': 0,
             'old_qualification_changed': False, 'new_model_generation': False, 'semantic_alignment_proven': False}
    _save(out / 'result.json', value)
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('audit-dev',))
    parser.parse_args()
    print(json.dumps(audit_dev(), ensure_ascii=False), flush=True)
