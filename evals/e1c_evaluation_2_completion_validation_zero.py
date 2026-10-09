"""New zero-call identity validating the sealed successful model patch, never editing it."""

from __future__ import annotations

import json
from unittest.mock import patch

from evals import e1c_evaluation_2_patch_probe_zero as probes
from evals import e1c_evaluation_2_public_precision_sweep as sweep
from evals import e1c_evaluation_2_thinking_completion_dev as paid
from evals import e1c_evaluation_2_three_arm_decode_audit as replay
from evals import e1c_evaluation_2_three_arm_dev as parent
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

OUT = ROOT / '.codex/e1c/evaluation_2/completion-public-validation-zero-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_COMPLETION_VALIDATION_ZERO_2026-10-09.md'


def run():
    if OUT.exists():
        raise FileExistsError('completion validation started; no retry')
    with paid.configured():
        frozen = parent._read(paid.OUT / 'freeze.json')
        if frozen != paid.preflight():
            raise ValueError('paid method/input identity changed')
        parent.verify_seal(paid.OUT)
        verified = parent._read(paid.OUT / 'verified-result.json')
        if verified['fixed_cells'] != 1 or len(verified['rows']) != 1 or verified['rows'][0]['resolved'] is not True:
            raise ValueError('one actually resolved model patch required')
        files = (paid.OUT / 'freeze.json', paid.OUT / 'generation-seal.json', paid.OUT / 'verified-result.json',
                 paid.OUT / 'strict_evidence/candidate.patch', ROOT / 'evals/e1c_evaluation_2_completion_validation_zero.py',
                 ROOT / 'evals/e1c_evaluation_2_patch_probe_zero.py', ROOT / 'evals/e1c_evaluation_2_public_precision_sweep.py', PROTOCOL)
        bindings = {p.relative_to(ROOT).as_posix(): _sha(p) for p in files}
        _save(OUT / 'freeze.json', {'bindings': bindings, 'provider_calls': 0, 'new_model_generation': False,
                                  'no_patch_or_probe_edits': True, 'new_namespace_not_original_score': True})
        with patch.object(replay, 'OUT', paid.OUT), patch.object(probes, 'OUT', OUT / 'own-probes'), patch.object(probes, 'PROTOCOL', PROTOCOL):
            own = probes.run()
            with patch.object(sweep, 'OUT', OUT / 'boundary'), patch.object(sweep, 'PROTOCOL', PROTOCOL):
                boundary = sweep.run()
        if any(_sha(ROOT / name) != digest for name, digest in bindings.items()):
            raise ValueError('sealed paid sources changed during zero validation')
    result = {'provider_calls': 0, 'new_model_generation': False,
              'own_control_completed_twice': own['unchanged_public_control_completed'],
              'own_target_completed_twice': own['unchanged_public_target_completed'],
              'variant_count': boundary['variant_count'], 'phase_completed': boundary['phase_completed'],
              'public_release_supported_gaps': boundary['patch_fails_where_public_release_completes'],
              'synthetic_variants_not_new_tasks': True, 'official_test_or_Gold_read': False,
              'full_issue_trusted': False, 'independent_generalization_claimed': False}
    _save(OUT / 'result.json', result)
    return result


if __name__ == '__main__':
    print(json.dumps(run()), flush=True)
