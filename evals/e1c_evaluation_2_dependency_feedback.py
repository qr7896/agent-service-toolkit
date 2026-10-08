"""Preserve pre-observer missing-source requests; zero-provider calibration only."""

from __future__ import annotations

import copy
import json

from evals import e1c_evaluation_2_scoped_controller as scope
from evals import e1c_evaluation_2_scoped_resume as resume
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

OUT = ROOT / '.codex/e1c/evaluation_2/dependency-feedback-zero-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_DEPENDENCY_FEEDBACK_PROTOCOL_2026-10-08.md'


def route(feedback):
    result = copy.deepcopy(feedback)
    verdict = result.get('controller_verdict', {})
    if verdict.get('status') != 'unknown_or_rejected_dependency_evidence':
        return result
    program = verdict['program']
    qualification = {'status': 'rejected' if program['rejected'] else 'unknown',
                     'rejected': program['rejected'], 'unknown': program['unknown'], 'program_evidence': program}
    gate = scope.action_gate({'qualification': qualification, 'behavior': {}, 'trusted_reproducer': False})
    previous = result.get('scope_gate', {})
    gate['rejected'] = sorted(set([*gate['rejected'], *previous.get('rejected', [])]))
    gate['missing_evidence'] = sorted(set([*gate['missing_evidence'], *previous.get('missing_evidence', [])]))
    if gate['rejected']:
        gate['action'] = 'REJECT'
    result['scope_gate'] = gate
    result['status'] = 'action_rejected' if gate['action'] == 'REJECT' else 'evidence_required_before_selection'
    scope.base.audit_repair_visible_payload(result)
    return result


def audit():
    if OUT.exists():
        raise FileExistsError('dependency feedback audit started; no retry')
    seal = json.loads((resume.OUT / 'generation-seal.json').read_bytes())
    if any(_sha(resume.OUT / n) != h for n, h in seal['files'].items()):
        raise ValueError('sealed generation changed')
    paths = sorted(resume.OUT.glob('*/turn-*/feedback.json'))
    _save(OUT / 'freeze.json', {'module_sha256': _sha(ROOT / 'evals/e1c_evaluation_2_dependency_feedback.py'),
                              'protocol_sha256': _sha(PROTOCOL), 'producer_seal_sha256': _sha(resume.OUT / 'generation-seal.json'),
                              'feedback_sha256': {p.relative_to(resume.OUT).as_posix(): _sha(p) for p in paths}, 'provider_calls': 0})
    rows = []
    for path in paths:
        original = json.loads(path.read_bytes())
        changed = route(original)
        if changed == original:
            continue
        rows.append({'source': path.relative_to(resume.OUT).as_posix(), 'old_source_requests': original['scope_gate']['bounded_source_requests'],
                     'source_requests': changed['scope_gate']['bounded_source_requests'], 'action': changed['scope_gate']['action'],
                     'repair_eligible': False, 'trusted_reproducer': False})
    result = {'rows': rows, 'provider_calls': 0, 'provider_tokens': 0, 'Gold_read': False, 'new_containers': 0,
              'shadow_audit_not_new_generation': True, 'old_scope_or_scores_changed': False, 'machine_trusted': 0}
    _save(OUT / 'result.json', result)
    return result


if __name__ == '__main__':
    print(json.dumps(audit(), ensure_ascii=False), flush=True)
