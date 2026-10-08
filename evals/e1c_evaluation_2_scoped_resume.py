"""Prefix-preserving continuation: no repeated provider request or old probe run."""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

import httpx
from langchain_core.messages import AIMessage

from agents.model_budget import ProviderBudgetExceeded, budgeted_ainvoke
from core.settings import settings
from evals import e1c_evaluation_2_feedback_projection as projection
from evals import e1c_evaluation_2_scoped_dev_trial as parent
from evals.e1c_evaluation_2_container_health import require_engine
from evals.e1c_evaluation_2_counterfactual_fast_dev import verify_workspace
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_raw_json import RawJsonFlash

ORIGINAL = parent.OUT
OUT = ROOT / '.codex/e1c/evaluation_2/scoped-controller-resume-v1'
SMOKE = ROOT / '.codex/e1c/evaluation_2/scoped-controller-resume-zero-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_SCOPED_RESUME_PROTOCOL_2026-10-08.md'
MODULES = (*parent.MODULES, 'evals/e1c_evaluation_2_feedback_projection.py', 'evals/e1c_evaluation_2_scoped_resume.py')
_preflight = parent.preflight


def ledger_usage(records):
    latest = {}
    for row in records:
        if row.get('run_id') != ORIGINAL.name or not row.get('call_id'):
            raise ValueError('ledger lineage differs')
        latest[row['call_id']] = row
    if any(r.get('status') != 'completed' for r in latest.values()):
        raise ValueError('unresolved provider request; continuation forbidden')
    usage = {}
    for row in latest.values():
        if type(row.get('total_tokens')) is not int or row['total_tokens'] <= 0:
            raise ValueError('exact provider token accounting required')
        item = usage.setdefault(row['task_id'], {'calls': 0, 'tokens': 0})
        item['calls'] += 1
        item['tokens'] += row['total_tokens']
    return usage


def prefix_plan():
    receipt = json.loads((ROOT / 'data/e1c_evaluation_2_scoped_dev_results.json').read_bytes())
    for name, digest in receipt['source_records'].items():
        if name.startswith(ORIGINAL.name + '/') and _sha(ORIGINAL.parent / name) != digest:
            raise ValueError('published interrupted prefix identity differs')
    old = json.loads((ORIGINAL / 'freeze.json').read_bytes())
    if any(_sha(ROOT / n) != h for n, h in old['method_sha256'].items()):
        raise ValueError('original frozen method source differs')
    state = json.loads((ORIGINAL / 'state.json').read_bytes())
    if state['status'] != 'interrupted_no_auto_retry' or state['error_type'] != 'BlindBoundaryViolation' or len(state['rows']) != 1:
        raise ValueError('exact interrupted state required')
    records = [json.loads(x) for x in (ORIGINAL / 'provider_calls.jsonl').read_text(encoding='utf-8').splitlines()]
    usage = ledger_usage(records)
    ids = [t['instance_id'] for t in old['tasks']]
    if len(ids) != 4 or state['rows'][0]['instance_id'] != ids[0] or state['rows'][0]['status'] != 'executed':
        raise ValueError('one completed ordered prefix required')
    if usage != {ids[0]: {'calls': 1, 'tokens': 3908}, ids[1]: {'calls': 2, 'tokens': 9798}}:
        raise ValueError('approved three-call prefix differs')
    files = {}
    for file in sorted(ORIGINAL.rglob('*')):
        if file.is_symlink() or 'gold-discrimination' in file.parts:
            raise ValueError('ungraded regular original prefix required')
        if file.is_file():
            files[file.relative_to(ORIGINAL).as_posix()] = _sha(file)
    return {'original_files': files, 'ledger_run_id': ORIGINAL.name, 'old_calls': 3, 'old_tokens': 13706,
            'additional_token_cap': 36294, 'max_additional_calls': 10, 'current_task': ids[1], 'cached_turns': 2,
            'current_remaining_tokens': 14202, 'current_remaining_calls': 2, 'completed_row': state['rows'][0]}


def preflight():
    plan = prefix_plan()
    value = _preflight()
    if value['batch_token_cap'] != 50000 or value['task_token_cap'] != 24000 or value['max_retries'] != 0:
        raise ValueError('original cumulative budget/retry contract required')
    if _sha(projection.OUT / 'result.json') != json.loads((ROOT / 'data/e1c_evaluation_2_scoped_dev_results.json').read_bytes())['source_records']['scope-feedback-projection-zero-v1/result.json']:
        raise ValueError('zero-call projection result differs')
    return {**value, 'schema': 'e1c2-scoped-resume-v1', 'resume_plan': plan,
            'prefix_replay_not_new_generation': True, 'projection_source_frozen': True,
            'resume_smoke_sha256': _sha(SMOKE / 'result.json'), 'resume_smoke_freeze_sha256': _sha(SMOKE / 'freeze.json')}


@contextmanager
def configured():
    with ExitStack() as stack:
        stack.enter_context(projection.configured())
        for key, value in [('OUT', OUT), ('PROTOCOL', PROTOCOL), ('MODULES', MODULES), ('preflight', preflight)]:
            stack.enter_context(patch.object(parent, key, value))
        stack.enter_context(parent.configured())
        yield parent.method.base.base._compiled


def cached_response(folder, turn):
    original = json.loads((folder / f'turn-{turn}/response.json').read_bytes())
    if original['response_status'] != 'received':
        raise RuntimeError('completed cached response missing')
    return AIMessage(content=original['raw'], usage_metadata={'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0})


@contextmanager
def cached_execution(loop, original, destination, cached_turns):
    delegate, seen = loop.execute_probe, []

    def execute(payload, frozen, workspace, image, root, environment, locked=None):
        turn = int(root.name.removeprefix('turn-'))
        if root.parent != destination or turn > cached_turns:
            if root.parent == destination and seen != list(range(1, cached_turns + 1)):
                raise RuntimeError('cached prefix incomplete before new probe')
            return delegate(payload, frozen, workspace, image, root, environment, locked)
        if turn != len(seen) + 1:
            raise RuntimeError('cached prefix order differs')
        folder = original / f'turn-{turn}'
        compiler = json.loads((folder / 'compiler.json').read_bytes())
        oracle = json.loads((folder / 'contract.json').read_bytes())['oracle']
        if payload != compiler['raw_contract'] or frozen != json.loads((folder / 'input.json').read_bytes()) or (locked is not None and locked != oracle):
            raise RuntimeError('cached payload/source/oracle prefix differs')
        feedback = projection.project_feedback(json.loads((folder / 'feedback.json').read_bytes()))
        execution = json.loads((folder / 'execution.json').read_bytes())
        _save(root / 'prefix-replay.json', {'original_response_sha256': _sha(folder / 'response.json'),
                                          'original_feedback_sha256': _sha(folder / 'feedback.json'),
                                          'original_execution_sha256': _sha(folder / 'execution.json'),
                                          'provider_calls': 0, 'containers_executed': 0, 'cached_not_new_generation': True})
        seen.append(turn)
        return feedback, oracle, None, execution

    with patch.object(loop, 'execute_probe', execute):
        yield seen


async def smoke():
    if SMOKE.exists():
        raise FileExistsError('resume smoke started; no retry')
    plan = prefix_plan()
    with configured() as compiled:
        task, initial, workspace = next(r for r in compiled.inputs() if r[0]['instance_id'] == plan['current_task'])
        _save(SMOKE / 'freeze.json', {'method_sha256': {n: _sha(ROOT / n) for n in MODULES},
                                    'protocol_sha256': _sha(PROTOCOL), 'original_files': plan['original_files'], 'provider_calls': 0})
        root, original = SMOKE / task['instance_id'], ORIGINAL / task['instance_id']
        checked = []

        async def invoke(messages, turn):
            if turn <= plan['cached_turns']:
                return cached_response(original, turn)
            prior = json.loads((root / f'turn-{turn - 1}/response.json').read_bytes())['raw']
            feedback = json.loads((root / f'turn-{turn - 1}/feedback.json').read_bytes())
            compiled.conversation(messages, turn, prior, feedback)
            checked.append(turn)
            return AIMessage(content='{"abstain_reason":"zero-call continuation checkpoint only"}',
                             usage_metadata={'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0})

        with cached_execution(compiled.base.loop, original, root, plan['cached_turns']) as seen:
            result = await compiled.base.loop.run_task(initial, workspace, task['image_id'], root, task['environment'], invoke)
        if seen != [1, 2] or checked != [3] or result['status'] != 'abstained':
            raise ValueError('actual zero-provider prefix continuation failed')
        value = {'prefix_turns_replayed_without_execution': seen, 'first_unstarted_turn_checked': 3,
                 'provider_calls': 0, 'new_containers': 0, 'original_prefix_unchanged': prefix_plan() == plan}
        _save(SMOKE / 'result.json', value)
        return value


def freeze():
    frozen_smoke = json.loads((SMOKE / 'freeze.json').read_bytes())
    if frozen_smoke['method_sha256'] != {n: _sha(ROOT / n) for n in MODULES} or frozen_smoke['protocol_sha256'] != _sha(PROTOCOL):
        raise ValueError('resume method differs after zero smoke')
    with configured():
        value = preflight()
        _save(OUT / 'freeze.json', value)
    return {'model': value['model'], 'additional_token_cap': 36294, 'max_additional_calls': 10, 'cumulative_token_cap': 50000}


async def run():
    with configured() as compiled:
        frozen = json.loads((OUT / 'freeze.json').read_bytes())
        if frozen != preflight() or (OUT / 'state.json').exists() or (OUT / 'provider_calls.jsonl').exists():
            raise RuntimeError('resume freeze differs or run already started; no retry')
        if not settings.DEEPSEEK_API_KEY:
            raise RuntimeError('credential unavailable')
        plan, tasks = frozen['resume_plan'], frozen['tasks']
        _save(OUT / 'started.json', {'original_prefix': plan['original_files'], 'provider_calls_before_resume': 3})
        shutil.copyfile(ORIGINAL / 'provider_calls.jsonl', OUT / 'provider_calls.jsonl')
        first = tasks[0]['instance_id']
        (OUT / first).mkdir()
        for name in ('candidate.json', 'execution.json'):
            shutil.copyfile(ORIGINAL / first / name, OUT / first / name)
        shutil.copytree(ORIGINAL / first / 'execution', OUT / first / 'execution')
        state = {'status': 'running', 'fixed_denominator': 12, 'admitted_denominator': 9, 'screen_denominator': 4,
                 'trusted_reproducer_count': 0, 'rows': [{**plan['completed_row'], 'origin': 'original_completed_prefix'}]}
        _save(OUT / 'state.json', state)

        def save_state():
            (OUT / 'state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

        try:
            async with httpx.AsyncClient(trust_env=False, timeout=120) as client:
                model = RawJsonFlash(model='deepseek-flash', temperature=0, streaming=False, max_retries=0,
                                     openai_api_base='https://api.deepseek.com', openai_api_key=settings.DEEPSEEK_API_KEY,
                                     http_async_client=client).bind(response_format={'type': 'json_object'})
                for index, (task, initial, workspace) in enumerate(compiled.inputs()):
                    if index == 0:
                        continue
                    iid, root = task['instance_id'], OUT / task['instance_id']
                    prefix_turns = plan['cached_turns'] if iid == plan['current_task'] else 0

                    async def invoke(messages, turn, task=task, workspace=workspace, initial=initial, root=root, index=index, prefix_turns=prefix_turns):
                        if turn <= prefix_turns:
                            return cached_response(ORIGINAL / task['instance_id'], turn)
                        if replayed != list(range(1, prefix_turns + 1)):
                            raise RuntimeError('cached prefix incomplete before provider')
                        require_engine((task['image_id'],))
                        verify_workspace(initial, workspace)
                        prior, feedback = None, None
                        if turn > 1:
                            prev = root / f'turn-{turn - 1}'
                            prior = json.loads((prev / 'response.json').read_bytes())['raw']
                            feedback = json.loads((prev / 'feedback.json').read_bytes())
                        print(json.dumps({'task': task['instance_id'], 'turn': turn, 'stage': 'new_unstarted_provider_budget_check'}), flush=True)
                        return await budgeted_ainvoke(model, compiled.conversation(messages, turn, prior, feedback), {'configurable': {
                            'provider_ledger_path': str(OUT / 'provider_calls.jsonl'), 'provider_run_id': plan['ledger_run_id'],
                            'provider_task_id': task['instance_id'], 'provider_total_token_ceiling': compiled.protected_ceiling(tasks, index),
                            'provider_task_token_ceiling': 24000, 'provider_max_calls_per_task': 4,
                            'provider_max_output_tokens': 2000, 'provider_prompt_reserve_multiplier': 1.4,
                            'provider_disable_thinking': True}}, role=f'e1c2_resume_turn_{turn}')

                    try:
                        with cached_execution(compiled.base.loop, ORIGINAL / iid, root, prefix_turns) as replayed:
                            row = await compiled.base.loop.run_task(initial, workspace, task['image_id'], root, task['environment'], invoke)
                    except ProviderBudgetExceeded as exc:
                        row = {'status': 'budget_stop_no_retry', 'reason': str(exc)[:300]}
                    state['rows'].append({'instance_id': iid, **row, 'origin': 'continued_prefix' if prefix_turns else 'previously_unstarted_task'})
                    save_state()
                    print(json.dumps({'task': iid, 'status': row['status']}), flush=True)
        except Exception as exc:
            state.update({'status': 'interrupted_no_auto_retry', 'error_type': type(exc).__name__})
            save_state()
            raise
        state['status'] = 'completed'
        save_state()
        if prefix_plan() != plan:
            raise RuntimeError('original prefix changed during continuation')
        compiled.base.seal()
        return {'status': state['status'], 'rows': [{'task': r['instance_id'], 'status': r['status'], 'origin': r['origin']} for r in state['rows']]}


def grade():
    with configured() as compiled:
        return compiled.grade()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('smoke', 'freeze', 'run', 'gold'))
    args = parser.parse_args()
    value = asyncio.run(smoke()) if args.command == 'smoke' else freeze() if args.command == 'freeze' else asyncio.run(run()) if args.command == 'run' else grade()
    print(json.dumps(value, ensure_ascii=False), flush=True)
