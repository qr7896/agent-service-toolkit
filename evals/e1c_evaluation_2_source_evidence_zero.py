"""Zero-provider, separately frozen Controller replay of two sealed OLD DEV probes."""

from __future__ import annotations

import json

from evals import e1c_evaluation_2_source_evidence_controller as method
from evals.e1c_evaluation_2_counterfactual_fast_dev import verify_workspace
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_issue_input import SOURCE

PARENT = method.previous.OUT
OUT = ROOT / '.codex/e1c/evaluation_2/source-evidence-controller-zero-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_SOURCE_EVIDENCE_ZERO_2026-10-08.md'
MODULES = (*method.previous.MODULES, 'evals/e1c_evaluation_2_source_evidence_controller.py',
           'evals/e1c_evaluation_2_source_evidence_zero.py', 'evals/e1c_evaluation_2_reference_scope.py',
           'evals/e1c_evaluation_2_export_chain.py', 'evals/e1c_evaluation_2_object_observer.py',
           'evals/e1c_evaluation_2_object_observer_v2.py')


def run():
    if OUT.exists():
        raise FileExistsError('zero source evidence replay started; no retry')
    parent = json.loads((PARENT / 'freeze.json').read_bytes())
    seal = json.loads((PARENT / 'generation-seal.json').read_bytes())
    if (any(_sha(ROOT / name) != digest for name, digest in parent['method_sha256'].items())
            or any(_sha(PARENT / name) != digest for name, digest in seal['files'].items())):
        raise ValueError('sealed parent identity differs')
    _save(OUT / 'freeze.json', {'modules': {p: _sha(ROOT / p) for p in MODULES}, 'protocol_sha256': _sha(PROTOCOL),
                              'parent_seal_sha256': _sha(PARENT / 'generation-seal.json'),
                              'provider_calls': 0, 'Gold_read': False, 'new_model_generation': False})
    rows = []
    try:
        with method.configured() as compiled, compiled.configured():
            compiled.inputs()  # Bind and verify original production workspaces/images.
            for task in parent['tasks']:
                iid = task['instance_id']
                files = sorted((PARENT / iid).glob('turn-*/compiler.json'))
                if not files:
                    raise ValueError('both existing library probe sources required')
                folder = files[-1].parent
                frozen = json.loads((folder / 'effective-input.json').read_bytes())
                payload = json.loads(files[-1].read_bytes())['raw_contract']
                workspace = SOURCE / iid
                verify_workspace(frozen, workspace)
                root = OUT / iid
                _save(root / 'input.json', frozen)
                result = compiled.base.loop.execute_probe(payload, frozen, workspace, task['image_id'], root, task['environment'])
                feedback, _, candidate, _ = result
                _save(root / 'feedback.json', feedback)
                q = feedback.get('controller_verdict', {}).get('qualification', {})
                # Confirm this new local evidence survives the real compact model-message boundary.
                messages = compiled.base.loop.messages(frozen, feedback)
                body = json.loads(messages[1].content)
                if body['last_feedback']['source_evidence'] != feedback['source_evidence']:
                    raise ValueError('new evidence absent from actual next Human')
                rows.append({'instance_id': iid, 'status': feedback['status'], 'exception_correspondence': q.get('exception_correspondence'),
                             'remaining_unknown': q.get('unknown', []), 'source_evidence': feedback['source_evidence'],
                             'limited_candidate_selected': candidate is not None, 'provider_calls': 0})
    except Exception as exc:
        _save(OUT / 'failure.json', {'error_type': type(exc).__name__, 'provider_calls': 0, 'no_retry': True})
        raise
    result = {'rows': rows, 'provider_calls': 0, 'provider_tokens': 0, 'Gold_read': False,
              'new_model_generation': False, 'cached_probe_replay_not_task_score': True, 'machine_trusted': 0}
    _save(OUT / 'result.json', result)
    return result


if __name__ == '__main__':
    print(json.dumps(run(), ensure_ascii=False), flush=True)
