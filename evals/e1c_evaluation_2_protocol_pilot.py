"""Two-source OLD DEV protocol pilot; one paid request per task, no retries."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from evals import e1c_evaluation_2_acquisition_dev as previous
from evals import e1c_evaluation_2_action_protocol as protocol
from evals import e1c_evaluation_2_ready_runtime_dev as codec
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

OUT = ROOT / '.codex/e1c/evaluation_2/action-protocol-flash-pilot-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_PROTOCOL_PILOT_2026-10-08.md'
MODULES = (*previous.MODULES, 'evals/e1c_evaluation_2_action_protocol.py',
           'evals/e1c_evaluation_2_protocol_pilot.py')
POLICY = protocol.policy()
BATCH_CAP, TASK_CAP = 20000, 12000
FAMILIES = ('scikit-learn__', 'marshmallow-code__')


def select_inputs(rows):
    # Preregister first admitted reference of each library, not manually chosen files.
    selected = []
    for family in FAMILIES:
        matching = [row for row in rows if row[0]['instance_id'].startswith(family)]
        if not matching:
            raise ValueError('both frozen OLD DEV library sources required')
        selected.append(matching[0])
    return selected


def parse_action(raw):
    codec._codec_proof.set(None)
    action, payload, proof = protocol.decode(raw, codec._issue.get())
    codec._codec_proof.set(proof)
    return action, payload


async def limited_invoke(invoke, model, messages, config, **kwargs):
    bounded = {**config, 'configurable': {**config['configurable'], 'provider_max_calls_per_task': 1}}
    return await invoke(model, messages, bounded, **kwargs)


def preflight():
    previous.previous.checked_parent()
    previous.checked_zero()
    checked = json.loads((protocol.OUT / 'freeze.json').read_bytes())
    if (checked['module_sha256'] != _sha(ROOT / 'evals/e1c_evaluation_2_action_protocol.py')
            or checked['protocol_sha256'] != _sha(protocol.PROTOCOL)):
        raise ValueError('zero-tested protocol identity changed')
    value = previous._preflight()
    if (value['model'] != 'deepseek-flash' or value['batch_token_cap'] != BATCH_CAP
            or value['task_token_cap'] != TASK_CAP or len(value['tasks']) != 2):
        raise ValueError('actual runner budget/cohort not wired')
    return {**value, 'schema': 'e1c2-action-protocol-flash-pilot-v1', 'screen_denominator': 2,
            'max_provider_calls': 2, 'max_calls_per_task': 1, 'input_hard_tokens': 24000,
            'conversation_chars_cap': 96000, 'full_admitted_DEV_run': False,
            'provider_purpose': 'OLD_DEV_PROTOCOL_DIAGNOSTIC_NOT_REPAIR',
            'real_provider_run_enabled': True, 'repair_or_canary_authorized': False,
            'selection_rule': 'first frozen reference per preregistered library family',
            'policy_sha256': hashlib.sha256(POLICY.encode()).hexdigest(),
            'decoder_hook': 'protocol.decode plus strict AST, quote refs and oracle',
            'no_auto_expansion': True}


@contextmanager
def configured():
    with ExitStack() as stack:
        stack.enter_context(patch.object(previous.adapter, 'POLICY', POLICY))
        for key, value in [('OUT', OUT), ('MODULES', MODULES), ('PROTOCOL', PROTOCOL)]:
            stack.enter_context(patch.object(previous, key, value))
        compiled = stack.enter_context(previous.configured())
        original_inputs, original_configured, original_invoke = compiled.inputs, compiled.configured, compiled.budgeted_ainvoke

        @contextmanager
        def runner_hooks():
            with original_configured(), patch.object(compiled.base.loop, 'parse_action', parse_action):
                yield

        async def invoke(model, messages, config, **kwargs):
            return await limited_invoke(original_invoke, model, messages, config, **kwargs)

        for key, value in [('CAP', BATCH_CAP), ('TASK_CAP', TASK_CAP), ('inputs', lambda: select_inputs(original_inputs())),
                           ('preflight', preflight), ('parse_action', parse_action), ('configured', runner_hooks),
                           ('budgeted_ainvoke', invoke)]:
            stack.enter_context(patch.object(compiled, key, value))
        yield compiled


def freeze():
    with configured() as compiled:
        value = preflight()
        # Inspect the actual nested hooks and final first-turn messages, not an unused helper.
        with compiled.configured():
            if compiled.base.loop.parse_action is not parse_action or compiled.base.loop.messages is not previous.adapter.messages:
                raise ValueError('actual nested action/message hooks differ')
            for _, initial, _ in compiled.inputs():
                messages = compiled.conversation(compiled.base.loop.messages(initial), 1)
                if messages[0].content != POLICY or 'production imports and fixture' in messages[0].content:
                    raise ValueError('code-bearing example remains in actual system message')
                body = json.loads(messages[1].content)
                if not body['windows'] or not body['public_issue_spans']:
                    raise ValueError('real issue and production evidence absent')
        _save(OUT / 'freeze.json', value)
    return {k: value[k] for k in ('schema', 'model', 'max_provider_calls', 'batch_token_cap', 'task_token_cap', 'max_retries')}


async def run():
    with configured() as compiled:
        return await compiled.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('freeze', 'run'))
    args = parser.parse_args()
    print(json.dumps(asyncio.run(run()) if args.command == 'run' else freeze(), ensure_ascii=False), flush=True)
