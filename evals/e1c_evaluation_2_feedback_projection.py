"""Zero-only projection of two known false diagnostic flags, never grader content."""

from __future__ import annotations

import copy
import json
from contextlib import contextmanager
from unittest.mock import patch

from evals import e1c_evaluation_2_scoped_controller as method
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

OUT = ROOT / '.codex/e1c/evaluation_2/scope-feedback-projection-zero-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_FEEDBACK_PROJECTION_PROTOCOL_2026-10-08.md'
_execute = method.execute_probe
SCHEMAS = {'qualification': {'e1c2-bounded-qualification-v2'}, 'behavior': {'e1c2-bounded-behavior-gate-v1'}}


def project_feedback(feedback):
    value = copy.deepcopy(feedback)
    verdict = value.get('controller_verdict', {})
    for name, schemas in SCHEMAS.items():
        record = verdict.get(name, {})
        if 'Gold_used' not in record:
            continue
        if record.get('schema') not in schemas or record['Gold_used'] is not False:
            raise ValueError('unrecognized or evaluator-bearing diagnostic metadata')
        del record['Gold_used']
    # No blacklist relaxation or blanket string/key scrubbing: real markers fail.
    method.base.audit_repair_visible_payload(value)
    return value


def execute_probe(*args, **kwargs):
    feedback, oracle, candidate, execution = _execute(*args, **kwargs)
    return project_feedback(feedback), oracle, candidate, execution


@contextmanager
def configured():
    with patch.object(method, 'execute_probe', execute_probe), method.configured():
        yield


def audit():
    from evals import e1c_evaluation_2_scoped_dev_trial as trial
    if OUT.exists():
        raise FileExistsError('feedback projection audit started; no retry')
    state = json.loads((trial.OUT / 'state.json').read_bytes())
    if state['status'] != 'interrupted_no_auto_retry' or state['error_type'] != 'BlindBoundaryViolation':
        raise ValueError('preserved boundary interruption required')
    tasks = json.loads((trial.OUT / 'freeze.json').read_bytes())['tasks']
    folders = [p for task in tasks for p in (trial.OUT / task['instance_id']).glob('turn-*/feedback.json')
               if 'controller_verdict' in json.loads(p.read_bytes())]
    if len(folders) != 1:
        raise ValueError('one recorded nonterminal Controller feedback required')
    feedback_path = folders[0]
    frozen = json.loads((feedback_path.parent / 'input.json').read_bytes())
    previous = json.loads((feedback_path.parent / 'compiler.json').read_bytes())['canonical_contract']
    original = json.loads(feedback_path.read_bytes())
    _save(OUT / 'freeze.json', {'module_sha256': _sha(ROOT / 'evals/e1c_evaluation_2_feedback_projection.py'),
                              'protocol_sha256': _sha(PROTOCOL), 'provider_calls': 0, 'Gold_read': False,
                              'failed_trial_freeze_sha256': _sha(trial.OUT / 'freeze.json'),
                              'failed_state_sha256': _sha(trial.OUT / 'state.json'),
                              'failed_ledger_sha256': _sha(trial.OUT / 'provider_calls.jsonl'),
                              'source_feedback_sha256': _sha(feedback_path)})
    projected = project_feedback(original)
    with configured(), trial.configured():
        compiled = trial.method.base.base._compiled
        compiled.inputs()  # Register verified source routes; no provider.
        if compiled.base.loop.execute_probe is not execute_probe:
            raise ValueError('projection hook overridden by nested configuration')
        messages = compiled.base.loop.messages(frozen, projected, previous)
        body = json.loads(messages[1].content)
        method.base.audit_repair_visible_payload(body)
    _save(OUT / 'agent-feedback.json', projected)
    result = {'schema': 'e1c2-feedback-projection-zero-v1', 'actual_human_message_boundary_passed': True,
              'nested_projection_hook_seen': True, 'known_false_diagnostic_flags_removed': 2,
              'scope_gate_unchanged': projected['scope_gate'] == original['scope_gate'],
              'unknown_still_requires_evidence': projected['status'] == 'evidence_required_before_selection',
              'human_message_chars': len(messages[1].content), 'projected_feedback_sha256': _sha(OUT / 'agent-feedback.json'),
              'provider_calls': 0, 'provider_tokens': 0, 'Gold_read': False, 'failed_trial_not_resumed': True,
              'new_containers': 0, 'machine_trusted': 0}
    _save(OUT / 'result.json', result)
    return result


if __name__ == '__main__':
    print(json.dumps(audit(), ensure_ascii=False), flush=True)
