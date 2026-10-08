"""One synthetic selected-candidate branch on the unchanged frozen Controller."""

from __future__ import annotations

import asyncio
import hashlib
import json

from langchain_core.messages import AIMessage

from evals import e1c_evaluation_2_qualified_controller as controller
from evals.e1c_evaluation_2_container_health import require_engine
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

OUT = ROOT / '.codex/e1c/evaluation_2/qualified-controller-failure-smoke-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_CONTROLLER_FAILURE_SMOKE_PROTOCOL_2026-10-08.md'


def synthetic_input(initial):
    quote = 'Please support `_e1c2_requested_flag` in `sklearn.ensemble.IsolationForest.__init__()`.\n'
    issue = quote + '_e1c2_requested_flag : bool, optional\n'
    frozen = {**initial, 'issue': issue, 'issue_sha256': hashlib.sha256(issue.encode()).hexdigest(), 'public_fixture_facts': []}
    payload = {'issue_quote': quote, 'expected_quote': quote, 'oracle': 'call_completes', 'assertion': '',
               'setup_source': 'from sklearn.ensemble import IsolationForest',
               'control_action': 'IsolationForest(n_estimators=2, random_state=0)',
               'target_action': 'IsolationForest(n_estimators=2, random_state=0, _e1c2_requested_flag=True)'}
    return frozen, payload


def validate(result, admission, verdict, controls, target):
    if (result['status'] != 'executed' or result['trusted_reproducer'] is not False
            or admission['decision'] != 'EXECUTE_UNCERTIFIED_DEV_CANDIDATE'
            or verdict['status'] != 'controller_qualification_recorded'
            or verdict['qualification']['status'] != 'mechanism_supported_candidate'
            or verdict['qualification']['unknown']
            or not verdict['behavior']['sub_obligation_supported']
            or verdict['trusted_reproducer'] is not False
            or any(len(c['runs']) != 1 or type(c['runs'][0]['returncode']) is not int
                   or c['runs'][0]['returncode'] != 0 or c['runs'][0]['timed_out'] for c in controls)
            or len(controls) != 2 or len(target['runs']) != 2
            or any(type(r['returncode']) is not int or r['returncode'] != 1 or r['timed_out'] for r in target['runs'])):
        raise ValueError('real synthetic selected-candidate Controller branch gate failed')


async def run():
    if OUT.exists():
        raise FileExistsError('failure smoke started; no automatic retry')
    frozen_method = json.loads((controller.OUT / 'freeze.json').read_bytes())
    if any(_sha(ROOT / name) != digest for name, digest in frozen_method['method_sha256'].items()):
        raise ValueError('frozen Controller source differs')
    with controller.configured():
        rows = controller.base._compiled.inputs()
        eligible = [(task, initial, workspace) for task, initial, workspace in rows
                    if any(w['path'].startswith('sklearn/') for w in initial['windows'])]
        if not eligible:
            raise ValueError('existing synthetic library fixture unavailable')
        task, initial, workspace = eligible[0]
        require_engine((task['image_id'],))
        _save(OUT / 'freeze.json', {'Controller_freeze_sha256': _sha(controller.OUT / 'freeze.json'),
                                  'driver_sha256': _sha(ROOT / 'evals/e1c_evaluation_2_controller_failure_smoke.py'),
                                  'protocol_sha256': _sha(PROTOCOL), 'provider_calls': 0, 'synthetic_not_task_score': True})
        frozen, payload = synthetic_input(initial)
        actions = [{'retrieve': 'IsolationForest.__init__'}, {'probe': payload}, {'abstain_reason': 'synthetic only'}]

        async def invoke(messages, turn):
            return AIMessage(content=json.dumps(actions[turn - 1]), usage_metadata={'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0})

        result = await controller.base._compiled.base.loop.run_task(frozen, workspace, task['image_id'], OUT / 'fixture', task['environment'], invoke)
        folder = OUT / 'fixture/turn-2'
        admission = json.loads((folder / 'controller-admission.json').read_bytes())
        verdict = json.loads((folder / 'controller-verdict.json').read_bytes())
        controls = [json.loads((folder / f'control-{n}.json').read_bytes()) for n in (1, 2)]
        target = json.loads((folder / 'execution.json').read_bytes())
        validate(result, admission, verdict, controls, target)
        observation = json.loads((folder / 'controller-observation/result.json').read_bytes())
        value = {'schema': 'e1c2-controller-real-failure-smoke-v1', 'synthetic_selected_branch_gate': True,
                 'provider_calls': 0, 'provider_tokens': 0, 'E1C_Gold_read': False, 'synthetic_not_task_score': True,
                 'control_returncodes': [0, 0], 'target_returncodes': [1, 1], 'observer_returncode': observation['returncode'],
                 'qualification_status': verdict['qualification']['status'], 'synthetic_sub_obligation_supported': True,
                 'full_issue_trusted': False, 'machine_trusted': 0, 'Controller_source_unchanged': True,
                 'verdict_sha256': _sha(folder / 'controller-verdict.json'), 'observation_sha256': _sha(folder / 'controller-observation/result.json')}
        _save(OUT / 'result.json', value)
        return value


if __name__ == '__main__':
    print(json.dumps(asyncio.run(run()), ensure_ascii=False), flush=True)
