"""Separate Flash OLD DEV trial; scope-gated candidates are never repair proofs."""

from __future__ import annotations

import argparse
import asyncio
import json
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from evals import e1c_evaluation_2_scoped_controller as method
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

PARENT, POSITIVE, FAILURE = method.OUT, method.SMOKE, method.FAILURE
PARENT_PROTOCOL = method.PROTOCOL
OUT = ROOT / '.codex/e1c/evaluation_2/scoped-controller-flash-dev-trial-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_SCOPED_DEV_TRIAL_PROTOCOL_2026-10-08.md'
MODULES = (*method.MODULES, 'evals/e1c_evaluation_2_controller_failure_smoke.py',
           'evals/e1c_evaluation_2_scoped_dev_trial.py', 'evals/e1c_evaluation_2_unified_dev_v2_gold.py')
_preflight = method.preflight


def checked_parent():
    frozen = json.loads((PARENT / 'freeze.json').read_bytes())
    if (any(_sha(ROOT / n) != h for n, h in frozen['method_sha256'].items())
            or _sha(PARENT_PROTOCOL) != frozen['protocol_sha256']
            or _sha(POSITIVE / 'result.json') != frozen['smoke_result_sha256']
            or _sha(POSITIVE / 'freeze.json') != frozen['smoke_freeze_sha256']):
        raise ValueError('parent method/protocol/positive smoke differs')
    failure = json.loads((FAILURE / 'freeze.json').read_bytes())
    if (failure['Controller_freeze_sha256'] != _sha(PARENT / 'freeze.json')
            or failure['driver_sha256'] != _sha(ROOT / 'evals/e1c_evaluation_2_controller_failure_smoke.py')
            or failure['protocol_sha256'] != _sha(PARENT_PROTOCOL)):
        raise ValueError('failure driver not bound to parent method')
    result = json.loads((FAILURE / 'result.json').read_bytes())
    gate = json.loads((FAILURE / 'scope-result.json').read_bytes())['scope_gate']
    if (result.get('synthetic_selected_branch_gate') is not True or result['provider_calls'] != 0
            or gate['action'] != 'INDEPENDENT_DEV_GRADE_ONLY' or gate['repair_eligible'] is not False):
        raise ValueError('real scope-gated synthetic branch required')
    return frozen


def preflight():
    checked_parent()
    value = _preflight()
    if (value['model'] != 'deepseek-flash' or value['batch_token_cap'] != 50000
            or value['max_provider_calls'] != 16 or value['max_retries'] != 0 or value['screen_denominator'] != 4):
        raise ValueError('exact bounded Flash four-reference trial required')
    return {**value, 'schema': 'e1c2-scoped-controller-flash-dev-trial-v1',
            'real_provider_run_enabled': True, 'provider_purpose': 'OLD_DEV_SCOPE_GATE_CALIBRATION_ONLY',
            'repair_or_canary_authorized': False, 'parent_freeze_sha256': _sha(PARENT / 'freeze.json'),
            'failure_smoke_sha256': _sha(FAILURE / 'result.json'), 'failure_scope_gate_sha256': _sha(FAILURE / 'scope-result.json')}


@contextmanager
def configured():
    with ExitStack() as stack:
        for key, value in [('OUT', OUT), ('PROTOCOL', PROTOCOL), ('MODULES', MODULES), ('preflight', preflight)]:
            stack.enter_context(patch.object(method, key, value))
        stack.enter_context(method.configured())
        yield


def freeze():
    with configured():
        value = preflight()
        _save(OUT / 'freeze.json', value)
        return {k: value[k] for k in ('schema', 'model', 'screen_denominator', 'batch_token_cap', 'max_provider_calls', 'max_retries', 'repair_or_canary_authorized')}


async def run():
    with configured():
        frozen = json.loads((OUT / 'freeze.json').read_bytes())
        if frozen != preflight() or frozen['repair_or_canary_authorized'] is not False:
            raise ValueError('new trial freeze differs')
        return await method.base.base._compiled.run()


def grade():
    with configured():
        return method.base.base._compiled.grade()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('freeze', 'run', 'gold'))
    args = parser.parse_args()
    value = asyncio.run(run()) if args.command == 'run' else grade() if args.command == 'gold' else freeze()
    print(json.dumps(value, ensure_ascii=False), flush=True)
