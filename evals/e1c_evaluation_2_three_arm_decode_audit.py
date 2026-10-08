"""Zero-call, post-hoc decoding/official scoring of sealed raw repair responses."""

from __future__ import annotations

import json
from unittest.mock import patch

from evals import e1c_evaluation_2_three_arm_dev as parent
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_issue_input import SOURCE

OUT = ROOT / '.codex/e1c/evaluation_2/three-arm-decoding-zero-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_THREE_ARM_DECODING_ZERO_2026-10-08.md'


def canonical_response(raw):
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError('response must be a JSON object')
    removed = False
    if set(value) == {'type', 'edits'} and value['type'] == 'json_object':
        value = {'edits': value['edits']}
        removed = True
    if set(value) != {'edits'}:
        raise ValueError('only edits and the exact known json_object envelope are allowed')
    # Never alter old/new/path strings; the unchanged parent parser owns edit validation.
    return json.dumps(value, ensure_ascii=False), removed


def run():
    if OUT.exists():
        raise FileExistsError('zero decoding audit started; no retry')
    frozen = parent._read(parent.OUT / 'freeze.json')
    if frozen != parent.preflight():
        raise ValueError('original method/input identity differs')
    parent.verify_seal(parent.OUT)
    if not (parent.OUT / 'result.json').is_file():
        raise ValueError('completed original result required')
    bindings = {p.relative_to(ROOT).as_posix(): _sha(p) for p in (
        parent.OUT / 'freeze.json', parent.OUT / 'generation-seal.json', parent.OUT / 'result.json',
        ROOT / 'evals/e1c_evaluation_2_three_arm_dev.py', ROOT / 'evals/e1c_evaluation_2_three_arm_decode_audit.py', PROTOCOL)}
    audit = {'schema': 'e1c2-posthoc-decoding-zero-v1', 'run_id': OUT.name,
             'instance_id': frozen['instance_id'], 'base_commit': frozen['base_commit'], 'image_id': frozen['image_id'],
             'bindings': bindings, 'provider_calls': 0, 'provider_tokens': 0,
             'new_model_generation': False, 'posthoc_not_original_frozen_method_score': True,
             'only_exact_known_envelope_removed': True, 'code_edit_strings_changed': False}
    _save(OUT / 'freeze.json', audit)
    _save(OUT / 'started.json', {'provider_calls': 0, 'not_new_generation': True})
    with (OUT / 'provider_calls.jsonl').open('xb'):
        pass  # Empty zero-call ledger; the original paid ledger stays sealed.
    rows = []
    for arm in parent.ARMS:
        input_data = parent._read(parent.OUT / arm / 'input.json')
        response = parent._read(parent.OUT / arm / 'response.json')
        _save(OUT / arm / 'input.json', input_data)
        _save(OUT / arm / 'response.json', response)
        try:
            normalized, removed = canonical_response(response['raw'])
            candidate = parent.compile_patch(normalized, input_data, SOURCE / frozen['instance_id'])
            with (OUT / arm / 'candidate.patch').open('xb') as handle:
                handle.write(candidate.encode())
            status = {'status': 'candidate' if candidate else 'abstained'}
            rows.append({'arm': arm, 'envelope_removed': removed, **status})
        except (ValueError, TypeError, SyntaxError, PermissionError) as exc:
            status = {'status': 'candidate_rejected', 'error_type': type(exc).__name__}
            rows.append({'arm': arm, **status})
        _save(OUT / arm / 'generation.json', status)
    _save(OUT / 'generation-seal.json', {'files': {p.relative_to(OUT).as_posix(): _sha(p)
          for p in OUT.rglob('*') if p.is_file()}, 'official_scoring_not_started': True})
    # Reuse only the independent scorer, scoped to this zero-call diagnostic identity.
    # No mutation of parent code, inputs, ledger, results, or frozen qualification.
    with patch.object(parent, 'OUT', OUT), patch.object(parent, 'preflight', lambda: audit):
        results = parent.grade()
    _save(OUT / 'audit-summary.json', {'decoding': rows, 'official': results, 'provider_calls': 0,
                                      'new_model_generation': False, 'original_results_not_rewritten': True})
    for name, digest in bindings.items():
        if _sha(ROOT / name) != digest:
            raise ValueError('original record/method changed during audit')
    return {'provider_calls': 0, 'decoding': rows, 'official_rows': results['rows'],
            'posthoc_not_original_frozen_method_score': True}


if __name__ == '__main__':
    print(json.dumps(run()), flush=True)
