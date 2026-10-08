"""Fresh four-reference Flash trial with actual acquisition and bounded 80k budget."""

from __future__ import annotations

import argparse
import asyncio
import json
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from evals import e1c_evaluation_2_acquisition_context as adapter
from evals import e1c_evaluation_2_scoped_dev_trial as previous
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

OUT = ROOT / '.codex/e1c/evaluation_2/acquisition-context-flash-dev-v1'
CHECK = ROOT / '.codex/e1c/evaluation_2/acquisition-context-zero-resume-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_ACQUISITION_DEV_PROTOCOL_2026-10-08.md'
MODULES = (*previous.MODULES, 'evals/e1c_evaluation_2_feedback_projection.py', 'evals/e1c_evaluation_2_dependency_feedback.py',
           'evals/e1c_evaluation_2_acquisition_context.py', 'evals/e1c_evaluation_2_acquisition_dev.py')
_preflight = previous.method.preflight


def checked_zero():
    frozen = json.loads((CHECK / 'check/freeze.json').read_bytes())
    if any(_sha(ROOT / name) != digest for name, digest in frozen['method_sha256'].items()):
        raise ValueError('zero-check method changed')
    outer = json.loads((CHECK / 'provenance-freeze.json').read_bytes())
    if _sha(ROOT / 'docs/research/E1C2_ACQUISITION_CHECK_RESUME_PROTOCOL_2026-10-08.md') != outer['protocol_sha256']:
        raise ValueError('zero-check protocol changed')
    result = json.loads((CHECK / 'result.json').read_bytes())
    if (result['provider_calls'] != 0 or len(result['acquisition_rows']) != 2
            or not all(r['next_message_exposes_source'] and r['initial_input_unchanged'] for r in result['acquisition_rows'])
            or not all(r['new_reserve'] < r['old_reserve'] for r in result['budget_rows'])):
        raise ValueError('real acquisition and reduced context gates required')
    return result


def preflight():
    previous.checked_parent()
    checked_zero()
    value = _preflight()
    if value['batch_token_cap'] != 80000 or value['task_token_cap'] != 48000 or value['model'] != 'deepseek-flash':
        raise ValueError('new budget not wired to actual runner')
    return {**value, 'schema': 'e1c2-acquisition-context-flash-dev-v1', 'real_provider_run_enabled': True,
            'provider_purpose': 'OLD_DEV_ACTUAL_ACQUISITION_CONTEXT_CALIBRATION',
            'input_soft_tokens': 12000, 'input_hard_tokens': 24000, 'task_soft_token_target': 32000,
            'batch_hard_tokens': 80000, 'task_hard_tokens': 48000, 'context_chars_cap': 96000, 'conversation_chars_cap': 96000,
            'max_automatic_symbols_per_issue_base': 2, 'repair_or_canary_authorized': False,
            'single_factor_causal_comparison': False, 'acquisition_check_sha256': _sha(CHECK / 'result.json'),
            'acquisition_check_freeze_sha256': _sha(CHECK / 'check/freeze.json')}


@contextmanager
def configured():
    with ExitStack() as stack:
        stack.enter_context(adapter.configured())
        for key, value in [('OUT', OUT), ('MODULES', MODULES), ('PROTOCOL', PROTOCOL), ('preflight', preflight)]:
            stack.enter_context(patch.object(previous, key, value))
        stack.enter_context(previous.configured())
        compiled = previous.method.base.base._compiled
        stack.enter_context(patch.object(compiled, 'CAP', adapter.BATCH_TOKENS))
        stack.enter_context(patch.object(compiled, 'TASK_CAP', adapter.TASK_HARD_TOKENS))
        yield compiled


def freeze():
    with configured():
        value = preflight()
        _save(OUT / 'freeze.json', value)
    return {k: value[k] for k in ('model', 'max_provider_calls', 'batch_token_cap', 'task_token_cap', 'input_hard_tokens', 'max_retries')}


async def run():
    with configured() as compiled:
        if json.loads((OUT / 'freeze.json').read_bytes()) != preflight():
            raise ValueError('new acquisition/budget freeze differs')
        return await compiled.run()


def grade():
    with configured() as compiled:
        return compiled.grade()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('freeze', 'run', 'gold'))
    args = parser.parse_args()
    value = asyncio.run(run()) if args.command == 'run' else grade() if args.command == 'gold' else freeze()
    print(json.dumps(value, ensure_ascii=False), flush=True)
