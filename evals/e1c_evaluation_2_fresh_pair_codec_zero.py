"""Zero-call post-hoc audit of exact known metadata envelopes, never rewrite paid results."""

from __future__ import annotations

import json

from evals import e1c_evaluation_2_fresh_pair_pipeline as parent
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_three_arm_decode_audit import canonical_response

OUT = ROOT / '.codex/e1c/evaluation_2/fresh-pair-codec-zero-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_FRESH_PAIR_CODEC_ZERO_2026-10-09.md'


def verify_parent():
    frozen = parent.edits._read(parent.OUT / 'freeze.json')
    if frozen != parent.preflight():
        raise ValueError('paid method or inputs changed')
    seal = parent.edits._read(parent.OUT / 'generation-seal.json')
    if not seal['official_scoring_not_started']:
        raise ValueError('generation did not precede scoring')
    for name, digest in seal['files'].items():
        path = (parent.OUT / name).resolve()
        if not path.is_relative_to(parent.OUT.resolve()) or _sha(path) != digest:
            raise ValueError('original producer seal changed')
    result = parent.edits._read(parent.OUT / 'result.json')
    expected = [r['instance_id'] for r in frozen['tasks']]
    if result['fixed_tasks'] != len(expected) or [r['instance_id'] for r in result['rows']] != expected:
        raise ValueError('completed original cohort required')
    return frozen


def run():
    if OUT.exists():
        raise FileExistsError('post-hoc codec audit started; no retry')
    verify_parent()
    bindings = {p.relative_to(ROOT).as_posix(): _sha(p) for p in (
        parent.OUT / 'freeze.json', parent.OUT / 'generation-seal.json', parent.OUT / 'result.json',
        parent.OUT / 'provider_calls.jsonl', ROOT / 'evals/e1c_evaluation_2_fresh_pair_codec_zero.py',
        ROOT / 'evals/e1c_evaluation_2_three_arm_decode_audit.py', PROTOCOL)}
    tasks = parent.inputs()
    parent.require_engine(tuple(r['image_id'] for r in tasks))
    _save(OUT / 'freeze.json', {'bindings': bindings, 'provider_calls': 0, 'new_model_generation': False,
        'posthoc_not_original_frozen_score': True, 'code_edit_strings_changed': False})
    rows, selected = [], []
    for row in tasks:
        iid = row['instance_id']
        origin, root = parent.OUT / iid, OUT / iid
        generation = parent.edits._read(origin / 'generation.json')
        response = origin / 'repair-call/response.json'
        status = {'instance_id': iid, 'status': 'not_eligible', 'patch_written': False}
        if generation['operational_pair_valid'] and response.is_file():
            record = parent.edits._read(response)
            if record['response_status'] == 'received':
                canonical, removed = canonical_response(record['raw'])
                if removed and not generation['patch_written']:
                    view = row['input']
                    body = {'production_windows': view['windows'], 'base_commit': view['base_commit'],
                            'allowed_production_paths': view['candidate_paths']}
                    candidate = parent.edits.compile_patch(canonical, body, SOURCE / iid)
                    _save(root / 'response.json', record)
                    _save(root / 'canonical.json', {'raw': canonical, 'only_known_envelope_removed': True})
                    _save(root / 'input.json', view)
                    (root / 'candidate.patch').write_bytes(candidate.encode())
                    status.update(status='decoded_candidate' if candidate else 'abstained', patch_written=bool(candidate))
                    if candidate:
                        runs = [parent.run_probe(parent.edits._read(origin / (phase + '-candidate.json')),
                                row, root / ('patch-' + phase), root / 'candidate.patch') for phase in ('normal', 'target')]
                        status['own_post_patch_pass'] = all(r['returncode'] == 0 for v in runs for r in v['runs'])
                        selected.append(row)
                else:
                    status['status'] = 'original_unchanged_not_rescored'
        _save(root / 'generation.json', status)
        rows.append(status)
    _save(OUT / 'generation-seal.json', {'files': {p.relative_to(OUT).as_posix(): _sha(p)
        for p in OUT.rglob('*') if p.is_file()}, 'official_scoring_not_started': True})
    seal = parent.edits._read(OUT / 'generation-seal.json')
    if any(_sha(OUT / name) != h for name, h in seal['files'].items()):
        raise ValueError('post-hoc seal changed before scoring')
    official = [parent.grade_one(row, OUT / row['instance_id']) for row in selected]
    verify_parent()
    if any(_sha(ROOT / name) != digest for name, digest in bindings.items()):
        raise ValueError('original records or zero method changed during audit')
    result = {'decoding': rows, 'official': official, 'newly_scored_candidates': len(selected),
        'provider_calls': 0, 'posthoc_not_original_frozen_score': True, 'original_results_unchanged': True,
        'full_issue_trusted': False, 'independent_generalization_claimed': False}
    _save(OUT / 'result.json', result)
    return result


if __name__ == '__main__':
    print(json.dumps(run()), flush=True)
