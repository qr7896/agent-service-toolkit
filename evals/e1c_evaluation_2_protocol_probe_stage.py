"""Planned probe stage from sealed, production-only pilot retrieval outputs."""

from __future__ import annotations

import argparse
import asyncio
import json
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from evals import e1c_evaluation_2_protocol_pilot as pilot
from evals.e1c_evaluation_2_counterfactual_fast_dev import verify_workspace
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

PARENT = pilot.OUT
PARENT_PROTOCOL = pilot.PROTOCOL
OUT = ROOT / '.codex/e1c/evaluation_2/action-protocol-flash-probe-stage-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_PROTOCOL_PROBE_STAGE_2026-10-08.md'
MODULES = (*pilot.MODULES, 'evals/e1c_evaluation_2_protocol_probe_stage.py')
_preflight = pilot.preflight


def checked_parent():
    frozen = json.loads((PARENT / 'freeze.json').read_bytes())
    seal = json.loads((PARENT / 'generation-seal.json').read_bytes())
    if (any(_sha(ROOT / name) != digest for name, digest in frozen['method_sha256'].items())
            or frozen['protocol_sha256'] != _sha(PARENT_PROTOCOL)
            or any(_sha(PARENT / name) != digest for name, digest in seal['files'].items())):
        raise ValueError('sealed protocol pilot changed')
    state = json.loads((PARENT / 'state.json').read_bytes())
    if state['status'] != 'completed' or len(state['rows']) != 2:
        raise ValueError('complete pilot required; never retry an interrupted trial')
    return frozen


def enriched_inputs(rows):
    checked_parent()
    result = []
    for task, initial, workspace in rows:
        folder = PARENT / task['instance_id']
        raw = json.loads((folder / 'turn-1/response.json').read_bytes())['raw']
        action, _, _ = pilot.protocol.decode(raw, initial['issue'])
        feedback = json.loads((folder / 'turn-1/feedback.json').read_bytes())
        if action != 'retrieve' or feedback.get('matches', 0) < 1:
            raise ValueError('stage requires actual successful production retrieval')
        path = folder / 'turn-2/input.json'
        enriched = json.loads(path.read_bytes())
        if enriched['issue'] != initial['issue'] or enriched['base_commit'] != initial['base_commit']:
            raise ValueError('cached retrieval changed issue/base identity')
        verify_workspace(enriched, workspace)
        result.append(({**task, 'parent_input_sha256': task['input_sha256'], 'input_sha256': _sha(path),
                        'input_origin': 'sealed_pilot_production_retrieval'}, enriched, workspace))
    return result


async def limited_invoke(invoke, model, messages, config, **kwargs):
    bounded = {**config, 'configurable': {**config['configurable'], 'provider_max_calls_per_task': 3}}
    return await invoke(model, messages, bounded, **kwargs)


def preflight():
    value = _preflight()
    return {**value, 'schema': 'e1c2-action-protocol-flash-probe-stage-v1', 'max_provider_calls': 6,
            'max_calls_per_task': 3, 'parent_generation_seal_sha256': _sha(PARENT / 'generation-seal.json'),
            'provider_purpose': 'OLD_DEV_EXECUTABLE_PROBE_DIAGNOSTIC_NOT_REPAIR',
            'cached_retrieval_not_new_model_success': True, 'full_issue_trust_gate_passed': False}


@contextmanager
def configured():
    with ExitStack() as stack:
        # Source and completed parent are never modified; only this process owns new hooks.
        for key, value in [('OUT', OUT), ('PROTOCOL', PROTOCOL), ('MODULES', MODULES), ('BATCH_CAP', 40000),
                           ('TASK_CAP', 24000), ('limited_invoke', limited_invoke)]:
            stack.enter_context(patch.object(pilot, key, value))
        compiled = stack.enter_context(pilot.configured())
        original = compiled.inputs
        stack.enter_context(patch.object(compiled, 'inputs', lambda: enriched_inputs(original())))
        stack.enter_context(patch.object(compiled, 'preflight', preflight))
        yield compiled


def freeze():
    with configured():
        value = preflight()
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
