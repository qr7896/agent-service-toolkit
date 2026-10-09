"""Snapshot-safe public boundary continuation and fresh issue-first OLD DEV localization."""

from __future__ import annotations

import argparse
import json
from unittest.mock import patch

from evals import e1c_evaluation_2_completion_validation_zero as prior
from evals import e1c_evaluation_2_patch_probe_zero as probes
from evals import e1c_evaluation_2_public_precision_sweep as sweep
from evals import e1c_evaluation_2_thinking_completion_dev as paid
from evals import e1c_evaluation_2_three_arm_decode_audit as replay
from evals import e1c_evaluation_2_three_arm_dev as parent
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_issue_input import OUT as ISSUES
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import freeze_input

BOUNDARY = ROOT / '.codex/e1c/evaluation_2/completion-boundary-snapshot-zero-v1'
LOCALIZE = ROOT / '.codex/e1c/evaluation_2/issue-first-two-source-localization-zero-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_COMPLETION_NEXT_ZERO_2026-10-09.md'


def source_bindings():
    names = ('evals/e1c_evaluation_2_completion_next_zero.py', 'evals/e1c_evaluation_2_probe.py',
             'evals/e1c_blind_evidence.py', 'evals/e1c_strict_v5_boundary.py')
    return {p: _sha(ROOT / p) for p in names} | {PROTOCOL.relative_to(ROOT).as_posix(): _sha(PROTOCOL)}


def validate_boundary():
    if BOUNDARY.exists():
        raise FileExistsError('snapshot boundary started; no retry')
    with paid.configured():
        frozen = parent._read(paid.OUT / 'freeze.json')
        if frozen != paid.preflight():
            raise ValueError('paid method/input changed')
        parent.verify_seal(paid.OUT)
        own = prior.OUT / 'own-probes'
        result = parent._read(own / 'result.json')
        if not result['unchanged_public_control_completed'] or not result['unchanged_public_target_completed']:
            raise ValueError('completed original public probes required')
        if (prior.OUT / 'boundary').exists():
            raise ValueError('original boundary unexpectedly started; no duplicate')
        bindings = source_bindings() | {p.relative_to(ROOT).as_posix(): _sha(p) for p in (
            paid.OUT / 'freeze.json', paid.OUT / 'generation-seal.json', paid.OUT / 'verified-result.json',
            paid.OUT / 'strict_evidence/candidate.patch', prior.OUT / 'freeze.json', own / 'result.json')}
        _save(BOUNDARY / 'dispatch-freeze.json', {'bindings': bindings, 'provider_calls': 0,
                                                'reuse_own_probe_without_replay': True,
                                                'verified_paid_snapshot_before_output_alias_patch': True})
        # Preflight is verified BEFORE changing the shared sweep output alias.
        # Otherwise the old input builder incorrectly reads the new output as its input.
        with patch.object(parent, 'preflight', lambda: frozen), patch.object(replay, 'OUT', paid.OUT), \
                patch.object(probes, 'OUT', own), patch.object(sweep, 'OUT', BOUNDARY), patch.object(sweep, 'PROTOCOL', PROTOCOL):
            result = sweep.run()
        if any(_sha(ROOT / name) != digest for name, digest in bindings.items()):
            raise ValueError('sealed dispatch/paid/probe sources changed')
        _save(BOUNDARY / 'verified-summary.json', {**result, 'original_failed_wrapper_not_rerun': True})
    return result


def localize():
    if LOCALIZE.exists():
        raise FileExistsError('issue-first localization started; no retry')
    tasks = parent._read(parent.source.PARENT / 'freeze.json')['tasks']
    if len(tasks) != 2:
        raise ValueError('two preregistered library references required')
    bindings = source_bindings() | {p.relative_to(ROOT).as_posix(): _sha(p) for p in (
        parent.source.PARENT / 'freeze.json', *(ISSUES / t['instance_id'] / 'problem_statement.md' for t in tasks))}
    _save(LOCALIZE / 'freeze.json', {'bindings': bindings, 'provider_calls': 0,
                                   'selection': 'both originally frozen library references, no new cohort',
                                   'fresh_issue_localization_not_old_effective_windows': True})
    rows = []
    for task in tasks:
        iid = task['instance_id']
        old = parent._read(parent.source.OUT / iid / 'effective-input.json')
        # Only base identity from prior records; no prior windows, probes, candidate
        # patches, source-site selection, or official outcomes are passed to retrieval.
        issue = (ISSUES / iid / 'problem_statement.md').read_text(encoding='utf-8')
        view = freeze_input(issue, SOURCE / iid, old['base_commit'], balanced=True)
        _save(LOCALIZE / iid / 'input.json', view)
        rows.append({'instance_id': iid, 'status': view['status'], 'window_count': len(view['windows']),
                     'source_paths': sorted(set(w['path'] for w in view['windows'])),
                     'input_sha256': _sha(LOCALIZE / iid / 'input.json'), 'provider_calls': 0})
        print(json.dumps(rows[-1]), flush=True)
    if any(_sha(ROOT / name) != digest for name, digest in bindings.items()):
        raise ValueError('localization source/protocol/issue changed')
    result = {'rows': rows, 'provider_calls': 0, 'new_model_generation': False,
              'fresh_issue_localization_completed': True, 'end_to_end_reproducer_or_repair_complete': False,
              'old_DEV_not_independent_canary': True, 'manual_task_file_map': False}
    _save(LOCALIZE / 'result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('validate-boundary', 'localize'))
    args = parser.parse_args()
    print(json.dumps(validate_boundary() if args.command == 'validate-boundary' else localize()), flush=True)
