"""Three-cell OLD DEV calibration with public counterexamples and base-bound globals."""

from __future__ import annotations

import argparse
import ast
import asyncio
import copy
import json
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from evals import e1c_evaluation_2_public_precision_sweep as sweep
from evals import e1c_evaluation_2_three_arm_dev as parent
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_three_arm_decode_audit import canonical_response

RUN_ID = 'e1c2-three-arm-public-boundary-dev-v2'
OUT = ROOT / '.codex/e1c/evaluation_2' / RUN_ID
PROTOCOL = ROOT / 'docs/research/E1C2_THREE_ARM_BOUNDARY_DEV_PROTOCOL_2026-10-08.md'
_inputs, _preflight, _compile, _record = parent.inputs, parent.preflight, parent.compile_patch, parent.response_record
SYSTEM = parent.SYSTEM + '''
The top-level response MUST have ONLY the key edits. Do not emit type, json_object tags, explanations or code fences.
Each nonempty edit must change production behavior; identical old and new strings are an abstention, not a repair.
Extra global definitions are exact-base source data, not proposed changes.
Static assignments may be conditionally rebound; they are NOT certified runtime values.
Public-derived counterexamples, when present, are synthetic hypotheses, not official test answers.
Use their own failures to check boundary coverage; an old release completing a probe does NOT prove value equivalence.
Do not revert legitimate functionality merely to copy the previous release, or install an optional dependency to hide a fallback defect.
'''


def loaded_globals(windows, workspace, base):
    output = []
    for name in sorted({w['path'] for w in windows}):
        raw = parent.source.method.qualified.git_blob(workspace, base, name)
        if len(raw) > 1_000_000:
            raise ValueError('production global source byte budget exceeded')
        tree = ast.parse(raw.decode())
        spans = [(w['start_line'], w['end_line']) for w in windows if w['path'] == name]
        references = {n.id for fn in ast.walk(tree) if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
                      and any(a <= fn.lineno and fn.end_lineno <= b for a, b in spans)
                      for n in ast.walk(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
        lines = raw.decode().splitlines()
        for node in tree.body:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.end_lineno - node.lineno > 15:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = {n.id for target in targets for n in ast.walk(target) if isinstance(n, ast.Name)}
            if not names.intersection(references) or any(a <= node.lineno and node.end_lineno <= b for a, b in spans):
                continue
            rebinding = [block for block in tree.body if block is not node
                         and not isinstance(block, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                         and any(isinstance(child, (ast.Assign, ast.AnnAssign, ast.AugAssign))
                                 and any(isinstance(target, ast.Name) and target.id in names for target in
                                         (child.targets if isinstance(child, ast.Assign) else [child.target]))
                                 for child in ast.walk(block))]
            start = min([node.lineno, *(block.lineno for block in rebinding)])
            end = max([node.end_lineno, *(block.end_lineno for block in rebinding)])
            complete_binding_context = end - start <= 15
            if not complete_binding_context:
                start, end = node.lineno, node.end_lineno
            output.append({'path': name, 'start_line': start, 'end_line': end,
                           'text': '\n'.join(lines[start - 1:end]),
                           'symbol': ','.join(sorted(names)), 'origin': 'base_bound_loaded_global_assignment',
                           'binding_may_be_reassigned': bool(rebinding), 'binding_context_complete': complete_binding_context,
                           'runtime_value_certified': False,
                           'source_sha256': next(w['source_sha256'] for w in windows if w['path'] == name)})
            if len(output) == 4:
                return output
    return output


def counterexamples(base_rows, release_rows, directory):
    old = {r['id']: r for r in release_rows}
    failures = [r for r in base_rows if r['returncode'] == 1 and old[r['id']]['returncode'] == 0]
    if len(failures) < 4:
        raise ValueError('four valid public-source counterexamples required')
    selected = failures[:2] + failures[-2:]
    return [{'id': r['id'], 'probe_source': (directory / (r['id'] + '.py')).read_text(encoding='utf-8'),
             'base_returncode': r['returncode'], 'public_release_returncode': old[r['id']]['returncode'],
             'base_failure_trace': r['stderr'][-900:], 'trace_truncated': len(r['stderr']) > 900,
             'synthetic_hypothesis_not_reported_input': True} for r in selected]


def inputs():
    task, bodies, bindings = _inputs()
    freeze = parent._read(sweep.OUT / 'freeze.json')
    if (freeze['bindings']['evals/e1c_evaluation_2_public_precision_sweep.py'] != _sha(ROOT / 'evals/e1c_evaluation_2_public_precision_sweep.py')
            or freeze['bindings'][str(sweep.PROTOCOL.relative_to(ROOT)).replace('\\', '/')] != _sha(sweep.PROTOCOL)):
        raise ValueError('public sweep method differs from frozen execution')
    root = sweep.OUT / 'variants'
    _, variants = sweep.variants(bodies['strict_evidence']['conditional_evidence']['own_target_probe'], bodies['standard']['issue'])
    for row in variants:
        if (root / (row['id'] + '.py')).read_bytes() != row['source'].encode():
            raise ValueError('synthetic public variant source changed')
    evidence = counterexamples(parent._read(sweep.OUT / 'base.json')['rows'],
                               parent._read(sweep.OUT / 'release.json')['rows'], root)
    globals_ = loaded_globals(bodies['standard']['production_windows'], SOURCE / task['instance_id'], bodies['standard']['base_commit'])
    bodies = augment_bodies(bodies, globals_, evidence)
    for name in ('freeze.json', 'base.json', 'release.json', 'result.json'):
        bindings[str((sweep.OUT / name).relative_to(ROOT))] = _sha(sweep.OUT / name)
    return task, bodies, bindings


def augment_bodies(bodies, globals_, evidence):
    # Separate copies: the original three arms deliberately share their immutable windows.
    output = {arm: copy.deepcopy(body) for arm, body in bodies.items()}
    for arm, body in output.items():
        body['production_windows'].extend(copy.deepcopy(globals_))
        if arm != 'standard':
            body['conditional_evidence']['public_boundary_counterexamples'] = evidence
            body['conditional_evidence']['counterexample_origin'] = 'public_literal_operator_base_and_public_release_runs_only'
    return output


def compile_patch(raw, body, workspace):
    normalized, _ = canonical_response(raw)
    return _compile(normalized, body, workspace)


def response_record(response):
    value = _record(response)
    try:
        _, removed = canonical_response(value['raw'])
    except (ValueError, TypeError):
        removed = None
    return {**value, 'exact_json_object_envelope_removed_by_new_decoder': removed}


def preflight():
    value = _preflight()
    return {**value, 'schema': 'e1c2-three-arm-public-boundary-dev-v2',
            'method_sha256': {p: _sha(ROOT / p) for p in (
                'evals/e1c_evaluation_2_three_arm_boundary_dev.py', 'evals/e1c_evaluation_2_three_arm_decode_audit.py',
                'evals/e1c_evaluation_2_public_precision_sweep.py')},
            'counterexamples_are_synthetic_DEV_only': True, 'global_definition_cap': 4,
            'no_official_failure_content_in_actor': True, 'previous_live_not_rerun': True}


@contextmanager
def configured():
    replacements = {'RUN_ID': RUN_ID, 'OUT': OUT, 'PROTOCOL': PROTOCOL, 'SYSTEM': SYSTEM,
                    'inputs': inputs, 'preflight': preflight, 'compile_patch': compile_patch, 'response_record': response_record}
    with ExitStack() as stack:
        for name, value in replacements.items():
            stack.enter_context(patch.object(parent, name, value))
        yield


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('preflight', 'run'))
    args = parser.parse_args()
    with configured():
        if args.command == 'preflight':
            frozen = preflight()
            if (OUT / 'freeze.json').exists():
                if parent._read(OUT / 'freeze.json') != frozen:
                    raise ValueError('existing boundary DEV freeze differs; do not overwrite')
            else:
                _save(OUT / 'freeze.json', frozen)
            print(json.dumps({'ready': True, 'cells': frozen['cells'], 'provider_calls': 0,
                              'model': frozen['model'], 'max_calls': 3, 'max_provider_tokens': parent.TOTAL_TOKENS}), flush=True)
        else:
            asyncio.run(parent.generate())
            print(json.dumps(parent.grade()), flush=True)


if __name__ == '__main__':
    main()
