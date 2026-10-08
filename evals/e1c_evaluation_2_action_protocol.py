"""Describe code-bearing fields without executable-looking placeholder values."""

from __future__ import annotations

import ast
import copy
import json

from evals import e1c_evaluation_2_acquisition_context as context
from evals import e1c_evaluation_2_ready_runtime_dev as codec
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

OUT = ROOT / '.codex/e1c/evaluation_2/action-protocol-zero-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_ACTION_PROTOCOL_ZERO_2026-10-08.md'

BEGIN = 'or {"probe":{"issue_quote_ref":0'
END = 'Replace placeholders; use exact public span IDs.'
FIELD_PROTOCOL = (
    'or one probe object. Probe fields: issue_quote_ref and expected_quote_ref are integer IDs of actual public spans; '
    'oracle is the string call_completes; setup_source, control_action and target_action must contain ACTUAL executable '
    'Python derived from the visible production APIs and public issue, not field descriptions or a schema example; '
    'assertion is the empty string. No example code values are supplied. Construct the real imports, supported normal '
    'configuration and target call yourself; if you cannot, retrieve missing production evidence or abstain.'
)


def policy():
    original = context.POLICY
    first = original.index(BEGIN)
    last = original.index(END, first) + len(END)
    return original[:first] + FIELD_PROTOCOL + original[last:]


def unwrap_action(value):
    if isinstance(value, dict) and set(value) == {'type', 'action'} and value['type'] == 'json_object' and isinstance(value['action'], dict):
        inner = value['action']
        if len(inner) == 1 and next(iter(inner)) in {'probe', 'retrieve', 'read', 'abstain_reason'}:
            return copy.deepcopy(inner)
    return value


def decode(raw, issue):
    # Existing strict field/ref/Python validation remains authoritative.
    value = unwrap_action(json.loads(raw))
    action, payload, proof = codec.decode(json.dumps(value, ensure_ascii=False), issue)
    if action == 'probe':
        for name in ('setup_source', 'control_action', 'target_action', 'assertion'):
            ast.parse(payload[name])  # Reject malformed descriptions before the Controller.
    return action, payload, proof


def check():
    from evals import e1c_evaluation_2_acquisition_dev as previous
    if OUT.exists():
        raise FileExistsError('action protocol check started; no retry')
    seal = json.loads((previous.OUT / 'generation-seal.json').read_bytes())
    if any(_sha(previous.OUT / n) != h for n, h in seal['files'].items()):
        raise ValueError('sealed model generation changed')
    _save(OUT / 'freeze.json', {'module_sha256': _sha(ROOT / 'evals/e1c_evaluation_2_action_protocol.py'),
                              'protocol_sha256': _sha(PROTOCOL), 'old_seal_sha256': _sha(previous.OUT / 'generation-seal.json'),
                              'provider_calls': 0})
    rows = []
    for path in sorted(previous.OUT.glob('*/turn-*/response.json')):
        raw = json.loads(path.read_bytes())['raw']
        value = json.loads(raw)
        unwrapped = unwrap_action(value)
        issue = json.loads((path.parent / 'input.json').read_bytes())['issue']
        try:
            action, _, _ = decode(raw, issue)
            status = 'valid_action_shape_and_syntax'
        except (ValueError, SyntaxError) as exc:
            action, status = None, type(exc).__name__
        rows.append({'source': path.relative_to(previous.OUT).as_posix(), 'wrapper_normalized': unwrapped != value,
                     'status': status, 'action': action})
    result = {'rows': rows, 'provider_calls': 0, 'provider_tokens': 0, 'new_containers': 0, 'Gold_read': False,
              'policy_has_no_code_example_values': 'production imports and fixture' not in policy(),
              'existing_code_not_repaired_or_invented': True, 'old_result_or_source_changed': False,
              'new_model_generation_not_run': True, 'machine_trusted': 0}
    _save(OUT / 'result.json', result)
    return result


if __name__ == '__main__':
    print(json.dumps(check(), ensure_ascii=False), flush=True)
