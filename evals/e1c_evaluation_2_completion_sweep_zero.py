"""Keep dispatch artifacts separate from a fresh legacy sweep execution directory."""

import json
from unittest.mock import patch

from evals import e1c_evaluation_2_completion_validation_zero as own
from evals import e1c_evaluation_2_patch_probe_zero as probes
from evals import e1c_evaluation_2_public_precision_sweep as sweep
from evals import e1c_evaluation_2_thinking_completion_dev as paid
from evals import e1c_evaluation_2_three_arm_decode_audit as replay
from evals import e1c_evaluation_2_three_arm_dev as parent
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

OUT = ROOT / '.codex/e1c/evaluation_2/completion-public-sweep-zero-v3'
PROTOCOL = ROOT / 'docs/research/E1C2_COMPLETION_SWEEP_ZERO_2026-10-09.md'


def run():
    if OUT.exists():
        raise FileExistsError('completion sweep dispatch started; no retry')
    with paid.configured():
        frozen = parent._read(paid.OUT / 'freeze.json')
        if frozen != paid.preflight():
            raise ValueError('paid identity changed')
        parent.verify_seal(paid.OUT)
        probe_root = own.OUT / 'own-probes'
        public = parent._read(probe_root / 'result.json')
        if not public['unchanged_public_control_completed'] or not public['unchanged_public_target_completed']:
            raise ValueError('completed public control/target required')
        bindings = {p.relative_to(ROOT).as_posix(): _sha(p) for p in (
            paid.OUT / 'generation-seal.json', paid.OUT / 'strict_evidence/candidate.patch',
            probe_root / 'result.json', ROOT / 'evals/e1c_evaluation_2_completion_sweep_zero.py', PROTOCOL)}
        _save(OUT / 'dispatch-freeze.json', {'bindings': bindings, 'provider_calls': 0,
                                           'no_prior_namespace_or_own_probe_replayed': True})
        execution = OUT / 'execution'  # Deliberately NOT created before legacy sweep.run().
        with patch.object(parent, 'preflight', lambda: frozen), patch.object(replay, 'OUT', paid.OUT), \
                patch.object(probes, 'OUT', probe_root), patch.object(sweep, 'OUT', execution), patch.object(sweep, 'PROTOCOL', PROTOCOL):
            result = sweep.run()
        if any(_sha(ROOT / n) != h for n, h in bindings.items()):
            raise ValueError('sealed sources changed')
        _save(OUT / 'result.json', result)
    return result


if __name__ == '__main__':
    print(json.dumps(run()), flush=True)
