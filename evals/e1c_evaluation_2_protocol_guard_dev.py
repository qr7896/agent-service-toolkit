"""Small OLD DEV iteration: safe frontier and no repeated successful retrieval."""

from __future__ import annotations

import argparse
import asyncio
import json
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from evals import e1c_evaluation_2_protocol_probe_stage as stage
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_protocol_execution import validate_frontier

OUT = ROOT / '.codex/e1c/evaluation_2/action-protocol-frontier-flash-dev-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_PROTOCOL_FRONTIER_DEV_2026-10-08.md'
MODULES = (*stage.MODULES, 'evals/e1c_evaluation_2_protocol_execution.py', 'evals/e1c_evaluation_2_protocol_guard_dev.py')
PREVIOUS_STAGE = stage.OUT
POLICY = stage.pilot.POLICY + (
    ' Shared setup executes in BOTH control and target. It must use base-supported APIs; unsupported requested '
    'configuration belongs inside target_action, not shared setup. Each phase must have its receiver defined. '
    'Do not rely on control mutations persisting into target, which executes separately. '
    'Inspect supplied windows before retrieving. If last_feedback.query has matches>0, do not retrieve that same '
    'query again. If the required definition is already visible, generate a real probe; otherwise request a '
    'different missing API or read an exposed production line. Missing evidence requires specific abstention, '
    'not repeated retrieval. Do not change public inputs or locked behavior to hide failure.'
)


def preflight():
    seal = json.loads((PREVIOUS_STAGE / 'generation-seal.json').read_bytes())
    if any(_sha(PREVIOUS_STAGE / name) != digest for name, digest in seal['files'].items()):
        raise ValueError('previous probe-stage generation changed')
    shadow = []
    for path in sorted(PREVIOUS_STAGE.glob('*/turn-*/compiler.json')):
        initial = json.loads((path.parent / 'input.json').read_bytes())
        payload = json.loads(path.read_bytes())['raw_contract']
        try:
            validate_frontier(payload, initial, SOURCE / path.parent.parent.name)
            status = 'no_binding_loss_detected'
        except ValueError as exc:
            if not str(exc).startswith('compiler_frontier_removes_control_binding:'):
                raise
            status = 'binding_loss_rejected_before_execution'
        shadow.append({'instance_id': path.parent.parent.name, 'status': status})
    if not shadow or not any(row['status'] == 'binding_loss_rejected_before_execution' for row in shadow):
        raise ValueError('actual previous receiver-loss regression not covered')
    return {**stage.preflight(), 'schema': 'e1c2-action-protocol-frontier-flash-dev-v1',
            'control_frontier_binding_guard': True, 'setup_execution_in_both_phases_explicit': True,
            'successful_retrieval_no_repeat_instruction': True, 'previous_probe_stage_seal_sha256':
                _sha(PREVIOUS_STAGE / 'generation-seal.json'), 'zero_provider_frontier_shadow': shadow}


@contextmanager
def configured():
    with ExitStack() as stack:
        stack.enter_context(patch.object(stage.pilot, 'POLICY', POLICY))
        for key, value in [('OUT', OUT), ('PROTOCOL', PROTOCOL), ('MODULES', MODULES)]:
            stack.enter_context(patch.object(stage, key, value))
        compiled = stack.enter_context(stage.configured())
        original_configured = compiled.configured

        @contextmanager
        def guarded_hooks():
            with original_configured():
                original_execute = compiled.base.loop.execute_probe

                def execute(payload, frozen, workspace, image, root, environment, locked=None):
                    proof = validate_frontier(payload, frozen, workspace)
                    _save(root / 'control-frontier-guard.json', proof)
                    return original_execute(payload, frozen, workspace, image, root, environment, locked)

                with patch.object(compiled.base.loop, 'execute_probe', execute):
                    yield

        stack.enter_context(patch.object(compiled, 'configured', guarded_hooks))
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
