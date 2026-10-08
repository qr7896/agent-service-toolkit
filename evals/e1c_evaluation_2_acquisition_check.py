"""Zero-provider actual dependency reads, message exposure and budget comparison."""

from __future__ import annotations

import copy
import json
import math
from unittest.mock import patch

from agents.model_budget import _prompt_text
from agents.model_router import estimate_tokens
from evals import e1c_evaluation_2_acquisition_context as adapter
from evals import e1c_evaluation_2_scoped_resume as previous
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

OUT = ROOT / '.codex/e1c/evaluation_2/acquisition-context-zero-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_ACQUISITION_CONTEXT_PROTOCOL_2026-10-08.md'


def reserve(messages):
    return math.ceil(estimate_tokens(_prompt_text(messages)) * 1.4) + adapter.OUTPUT_TOKENS


def run():
    if OUT.exists():
        raise FileExistsError('acquisition/context check already started; no retry')
    seal = json.loads((previous.OUT / 'generation-seal.json').read_bytes())
    if any(_sha(previous.OUT / n) != h for n, h in seal['files'].items()):
        raise ValueError('previous generation seal differs')
    modules = [*previous.MODULES, 'evals/e1c_evaluation_2_dependency_feedback.py',
               'evals/e1c_evaluation_2_acquisition_context.py', 'evals/e1c_evaluation_2_acquisition_check.py']
    _save(OUT / 'freeze.json', {'method_sha256': {n: _sha(ROOT / n) for n in modules}, 'protocol_sha256': _sha(PROTOCOL),
                              'old_generation_seal_sha256': _sha(previous.OUT / 'generation-seal.json'),
                              'provider_calls': 0, 'input_soft_tokens': 12000, 'input_hard_tokens': 24000,
                              'task_soft_tokens': 32000, 'task_hard_tokens': 48000, 'batch_tokens': 80000})
    before = []
    state = json.loads((previous.OUT / 'state.json').read_bytes())
    with previous.configured() as old:
        old.inputs()
        for task in state['rows']:
            if task['status'] != 'budget_stop_no_retry':
                continue
            folder = previous.OUT / task['instance_id']
            frozen = json.loads((folder / 'turn-4/input.json').read_bytes())
            raw = json.loads((folder / 'turn-3/response.json').read_bytes())['raw']
            feedback = json.loads((folder / 'turn-3/feedback.json').read_bytes())
            payload = json.loads((folder / 'turn-3/compiler.json').read_bytes())['raw_contract']
            before.append((task['instance_id'], frozen, raw, feedback, payload,
                           reserve(old.conversation(old.base.loop.messages(frozen, feedback, payload), 4, raw, feedback))))
    acquired, budgets = [], []
    with adapter.configured(), previous.configured() as compiled:
        rows = compiled.inputs()
        for task, initial, workspace in rows:
            iid = task['instance_id']
            paths = sorted((previous.OUT / iid).glob('turn-*/feedback.json'))
            for path in paths:
                feedback = json.loads(path.read_bytes())
                if not adapter.program(feedback).get('unexposed_dependency_bindings'):
                    continue
                frozen = json.loads((path.parent / 'input.json').read_bytes())
                payload = json.loads((path.parent / 'compiler.json').read_bytes())['raw_contract']
                original = copy.deepcopy(frozen)
                oracle = json.loads((path.parent / 'contract.json').read_bytes())['oracle']
                execution = json.loads((path.parent / 'execution.json').read_bytes())
                destination = OUT / 'acquisition' / iid
                # Only the original probe delegate is cached; acquisition itself is real.
                with patch.object(adapter, '_execute', lambda *args: (feedback, oracle, None, execution)):
                    result = compiled.base.loop.execute_probe(payload, frozen, workspace, task['image_id'], destination, task['environment'])
                visible = adapter.effective(frozen)
                human = json.loads(compiled.base.loop.messages(frozen, result[0], payload)[1].content)
                records = result[0].get('automatic_source_acquisition', [])
                if frozen != original or not records or not all(any(w['path'] == r.get('path') for w in human['windows'])
                                                                for r in records if r['status'] == 'production_window_acquired'):
                    raise ValueError('actual automatic source exposure did not complete')
                _save(destination / 'effective-next-input.json', visible)
                acquired.append({'instance_id': iid, 'records': records, 'next_message_exposes_source': True,
                                 'initial_input_unchanged': True, 'probe_delegate_cached_not_reexecuted': True,
                                 'trusted_reproducer': False})
                break
        for iid, frozen, raw, feedback, payload, old_reserve in before:
            msgs = compiled.base.loop.messages(frozen, feedback, payload)
            full = compiled.conversation(msgs, 4, raw, feedback)
            current = reserve(full)
            budgets.append({'instance_id': iid, 'old_reserve': old_reserve, 'new_reserve': current,
                            'estimated_input_tokens': estimate_tokens(_prompt_text(full)),
                            'windows_include_automatic_acquisition': len(adapter.effective(frozen)['windows']) >= len(frozen['windows']),
                            'scope_or_behavior_not_promoted': True})
    if len(acquired) != 2 or len(budgets) != 2:
        raise ValueError('complete missing-source and two budget-stop checks required')
    result = {'acquisition_rows': acquired, 'budget_rows': budgets, 'provider_calls': 0, 'provider_tokens': 0,
              'new_containers': 0, 'Gold_read': False, 'old_scores_or_source_modified': False, 'machine_trusted': 0,
              'cached_delegate_not_new_generation': True, 'real_model_behavior_not_yet_verified': True}
    _save(OUT / 'result.json', result)
    return result


if __name__ == '__main__':
    print(json.dumps(run(), ensure_ascii=False), flush=True)
