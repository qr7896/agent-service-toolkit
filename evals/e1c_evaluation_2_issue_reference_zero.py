"""Supplement fresh OLD DEV windows using qualified names literally present in public issue."""

import json
import re

from evals import e1c_evaluation_2_completion_next_zero as previous
from evals import e1c_evaluation_2_three_arm_dev as parent
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_public_api_windows import resolve_method, resolve_symbol, window
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

OUT = ROOT / '.codex/e1c/evaluation_2/issue-qualified-reference-zero-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_ISSUE_REFERENCE_ZERO_2026-10-09.md'


def references(issue):
    literals = re.findall(r'`([^`]+)`', issue)
    return list(dict.fromkeys(s for s in literals if re.fullmatch(r'(?:[A-Za-z_]\w*\.)+[A-Za-z_]\w*', s)))[:4]


def supplement(view, workspace):
    additions, rows = [], []
    for reference in references(view['issue']):
        module, symbol = reference.rsplit('.', 1)
        definition = resolve_symbol(workspace, module, symbol)
        if definition is None:
            rows.append({'reference': reference, 'status': 'unresolved', 'semantic_binding_certified': False})
            continue
        # Constructor then declaration; both are bounded existing AST windows.
        constructor = resolve_method(workspace, definition, '__init__')
        for record in [r for r in (constructor, definition) if r is not None]:
            name = record['path'].relative_to(workspace).as_posix()
            raw = record['path'].read_bytes()
            if raw.replace(b'\r\n', b'\n') != parent.source.method.qualified.git_blob(workspace, view['base_commit'], name):
                raise ValueError('resolved public definition differs from base')
            item = window(record, workspace)
            item['origin'] = 'public_issue_qualified_definition'
            item['seed'] = {'reference': reference, 'literal_in_public_issue': True}
            key = (item['path'], item['symbol'], item.get('owner'))
            if not any((w['path'], w.get('symbol'), w.get('owner')) == key for w in [*view['windows'], *additions]):
                if len(additions) < 4:
                    additions.append(item)
        rows.append({'reference': reference, 'status': 'base_definition_found', 'path': name,
                     'semantic_binding_certified': False})
    output = {**view, 'windows': [*view['windows'], *additions], 'public_reference_audit': rows,
              'schema': 'e1c2-issue-qualified-reference-input-v1', 'source_retrieval_not_semantic_certificate': True}
    audit_repair_visible_payload(output)
    return output, rows, len(additions)


def run():
    if OUT.exists():
        raise FileExistsError('qualified reference zero started; no retry')
    original = parent._read(previous.LOCALIZE / 'result.json')
    bindings = {p.relative_to(ROOT).as_posix(): _sha(p) for p in (
        previous.LOCALIZE / 'freeze.json', previous.LOCALIZE / 'result.json',
        ROOT / 'evals/e1c_evaluation_2_issue_reference_zero.py', ROOT / 'evals/e1c_evaluation_2_public_api_windows.py', PROTOCOL)}
    _save(OUT / 'freeze.json', {'bindings': bindings, 'provider_calls': 0, 'reference_cap': 4, 'additional_window_cap': 4})
    rows = []
    for row in original['rows']:
        iid = row['instance_id']
        path = previous.LOCALIZE / iid / 'input.json'
        if _sha(path) != row['input_sha256']:
            raise ValueError('fresh issue/source input changed')
        value, audit, count = supplement(parent._read(path), SOURCE / iid)
        _save(OUT / iid / 'input.json', value)
        rows.append({'instance_id': iid, 'additional_windows': count, 'window_count': len(value['windows']),
                     'references': audit, 'input_sha256': _sha(OUT / iid / 'input.json'), 'provider_calls': 0})
        print(json.dumps(rows[-1]), flush=True)
    if any(_sha(ROOT / n) != h for n, h in bindings.items()):
        raise ValueError('source identity changed during supplement')
    result = {'rows': rows, 'provider_calls': 0, 'new_model_generation': False, 'manual_task_file_map': False,
              'source_retrieval_not_full_method_or_semantic_proof': True}
    _save(OUT / 'result.json', result)
    return result


if __name__ == '__main__':
    print(json.dumps(run()), flush=True)
