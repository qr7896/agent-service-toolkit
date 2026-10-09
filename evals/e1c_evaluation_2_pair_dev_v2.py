"""Fresh DEV continuation: preregistered codec, real dependency conditions, no global aliases."""

from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import json
import math

from agents.model_budget import ProviderBudgetExceeded, _events, _prompt_text, budgeted_ainvoke
from agents.model_router import estimate_tokens
from evals import e1c_evaluation_2_fresh_pair_pipeline as shared
from evals import e1c_evaluation_2_issue_reference_zero as reference
from evals.e1c_evaluation_2 import IDENTITY
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_issue_input import OUT as ISSUES
from evals.e1c_evaluation_2_issue_input import SOURCE, TREE
from evals.e1c_evaluation_2_metadata import OUT as METADATA
from evals.e1c_evaluation_2_probe import freeze_input
from evals.e1c_evaluation_2_three_arm_decode_audit import canonical_response

RUN_ID = 'e1c2-pair-dev-v2'
OUT = ROOT / '.codex/e1c/evaluation_2' / RUN_ID
PREP = ROOT / '.codex/e1c/evaluation_2/pair-dev-v2-inputs-zero-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_PAIR_DEV_V2_PROTOCOL_2026-10-09.md'
GRADER = ROOT / '.codex/e1c/evaluation_2/grader-only'
PROBE_SYSTEM = shared.PROBE_SYSTEM + '''
Do not assign to imported module attributes or rebind imported names to manufacture a failure condition.
Explicitly missing dependencies are blocked by the executor. Do not change a library's availability guard.
'''


def validate_source(view, workspace):
    for window in view['windows']:
        shared.assert_production_relative_path(window['path'])
        shared.edits.source.method.checked_source(view, workspace, window['path'])
        blob = shared.edits.source.method.qualified.git_blob(workspace, view['base_commit'], window['path']).decode()
        lines = blob.splitlines()
        slices = window.get('source_slices') or [{'start_line': window['start_line'], 'end_line': window['end_line']}]
        text = '\n'.join('\n'.join(lines[s['start_line'] - 1:s['end_line']]) for s in slices)
        cap = 2500 if window.get('source_slices') else 2200 if window['origin'] == 'issue_lexical' else 5000
        if window['text'].rstrip('\n') != text[:cap].rstrip('\n'):
            raise ValueError('window is not its exact base slice')


def prepare():
    if PREP.exists():
        raise FileExistsError('DEV input preparation already started; no retry')
    identity, metadata = shared.edits._read(IDENTITY), shared.edits._read(METADATA)
    tree = shared.edits._read(TREE)  # Public blob IDs only; never load test or Gold content.
    if (identity['role'] != 'development_only_never_independent_canary_or_fresh30'
            or len(identity['tasks']) != 12 or metadata['identity_sha256'] != _sha(IDENTITY)
            ):
        raise ValueError('frozen DEV12 provenance differs')
    if len({identity['source_revision'], metadata['source_revision'], tree['source_revision']}) != 1:
        raise ValueError('public source revisions differ')
    bindings = {p.relative_to(ROOT).as_posix(): _sha(p) for p in (
        IDENTITY, METADATA, TREE, shared.OUT / 'freeze.json', PROTOCOL,
        ROOT / 'evals/e1c_evaluation_2_pair_dev_v2.py', ROOT / 'evals/e1c_evaluation_2_issue_input.py')}
    bindings.update({p.relative_to(ROOT).as_posix(): _sha(p) for t in identity['tasks']
        for phase in ('base', 'gold') if (p := GRADER / t['instance_id'] / (phase + '.json')).is_file()})
    _save(PREP / 'freeze.json', {'bindings': bindings, 'provider_calls': 0, 'fixed_DEV_tasks': 12})
    rows = []
    for frozen_task in identity['tasks']:
        iid = frozen_task['instance_id']
        task = next(r for r in metadata['tasks'] if r['instance_id'] == iid)
        workspace, issue = SOURCE / iid, ISSUES / iid / 'problem_statement.md'
        row = {'instance_id': iid, 'repo': task['repo'], 'status': 'INFRA_BLOCKED', 'provider_calls': 0}
        if workspace.is_dir() and issue.is_file():
            raw = issue.read_bytes()
            blob = hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()
            if tree['sha'].get(f'tasks/{iid}/problem_statement.md') != blob:
                raise ValueError('public issue blob differs')
            view = freeze_input(raw.decode(), workspace, task['base_commit'], balanced=True)
            view, _, _ = reference.supplement(view, workspace)
            validate_source(view, workspace)
            if not any(w['path'].split('/')[0] not in {'benchmarks', 'examples'} for w in view['windows']):
                row['status'] = 'no_production_candidate'
                rows.append(row)
                print(json.dumps(row), flush=True)
                continue
            view['windows'].extend(shared.globals_method.loaded_globals(view['windows'], workspace, view['base_commit']))
            view = shared.canonical_input(view)
            if len(shared.input_json(view)) > 32000:
                row['status'] = 'context_budget_exceeded'
            else:
                _save(PREP / iid / 'input.json', view)
                admitted = all((GRADER / iid / (phase + '.json')).is_file()
                    and shared.edits._read(GRADER / iid / (phase + '.json')).get('phase_pass') is True
                    for phase in ('base', 'gold'))
                row.update(status='ready', admitted=admitted, input_sha256=_sha(PREP / iid / 'input.json'),
                    image_id=shared.verified_local_image(iid), issue_blob=blob, canonical_input_sha256=view['input_sha256'])
        rows.append(row)
        print(json.dumps(row), flush=True)
    if any(_sha(ROOT / p) != h for p, h in bindings.items()):
        raise ValueError('source metadata or method changed during preparation')
    result = {'fixed_DEV_tasks': 12, 'rows': rows, 'provider_calls': 0, 'official_or_Gold_content_in_actor': False}
    _save(PREP / 'result.json', result)
    return result


def selected_rows():
    frozen = shared.edits._read(PREP / 'freeze.json')
    if any(_sha(ROOT / p) != h for p, h in frozen['bindings'].items()):
        raise ValueError('prepared source identity differs')
    rows = shared.edits._read(PREP / 'result.json')['rows']
    prior = {r['instance_id'] for r in shared.edits._read(shared.OUT / 'freeze.json')['tasks']}
    selected, repos = [], set()
    # Deterministic frozen order, unseen-in-this-pipeline first task per repository;
    # no ranking by repair outcomes, test content, or hand-selected source files.
    for row in rows:
        if row['status'] != 'ready' or not row['admitted'] or row['instance_id'] in prior or row['repo'] in repos:
            continue
        selected.append(row)
        repos.add(row['repo'])
        if len(selected) == 2:
            break
    if len(selected) != 2:
        raise ValueError('two next admitted repository representatives required')
    for row in selected:
        path = PREP / row['instance_id'] / 'input.json'
        if _sha(path) != row['input_sha256']:
            raise ValueError('prepared input artifact changed')
        view = shared.edits._read(path)
        validate_source(view, SOURCE / row['instance_id'])
        if view['input_sha256'] != shared.canonical_input(view)['input_sha256']:
            raise ValueError('canonical identity changed')
        row['input'] = view
        row['missing_optional_import'] = shared.issue_missing_optional_import(view)
    return selected


def messages(view, phase, evidence=None):
    value = shared.messages(view, phase, evidence)
    if phase == 'probe':
        value[0].content = PROBE_SYSTEM
    return value


def validate_pair(raw, view, workspace):
    candidates = shared.validate_pair(raw, view, workspace)
    for candidate in candidates.values():
        tree = ast.parse(candidate['source'])
        imported = {alias.asname or alias.name.split('.')[0] for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
        namespace_aliases = set(imported)
        assignments = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)]
        for _ in assignments:
            for assignment in assignments:
                if isinstance(assignment.value, ast.Name) and assignment.value.id in namespace_aliases:
                    namespace_aliases.update(t.id for t in assignment.targets if isinstance(t, ast.Name))
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in imported and isinstance(node.ctx, ast.Store):
                raise ValueError('probe rebinds an imported name')
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {'setattr', 'delattr'}
                    and node.args and isinstance(node.args[0], ast.Name) and node.args[0].id in namespace_aliases):
                raise ValueError('probe writes through an imported namespace')
            targets = node.targets if isinstance(node, (ast.Assign, ast.Delete)) else [node.target] if isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)) else []
            for target in targets:
                for part in ast.walk(target):
                    if isinstance(part, ast.Name) and part.id in imported and isinstance(part.ctx, ast.Store):
                        raise ValueError('probe rebinds an imported name')
                root = target
                while isinstance(root, (ast.Attribute, ast.Subscript)):
                    root = root.value
                if isinstance(target, (ast.Attribute, ast.Subscript)) and isinstance(root, ast.Name) and root.id in namespace_aliases:
                    raise ValueError('probe writes through an imported namespace')
    return candidates


def preflight():
    tasks = []
    for row in selected_rows():
        prompt = _prompt_text(messages(row['input'], 'probe'))
        reserve = math.ceil(estimate_tokens(prompt) * 1.4) + shared.MAX_OUTPUT
        if reserve > shared.TASK:
            raise ValueError('initial request exceeds per-task reserve')
        tasks.append({k: v for k, v in row.items() if k != 'input'} | {
            'initial_prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(), 'initial_reserve': reserve})
    names = (*shared.MODULES, 'evals/e1c_evaluation_2_pair_dev_v2.py',
             'evals/e1c_evaluation_2_issue_input.py', 'evals/e1c_evaluation_2_three_arm_decode_audit.py')
    return {'run_id': RUN_ID, 'tasks': tasks, 'fixed_tasks': 2, 'DEV_pool_tasks': 12,
        'max_calls': 4, 'max_provider_tokens': shared.TOTAL, 'per_task_tokens': shared.TASK,
        'max_output_tokens': shared.MAX_OUTPUT, 'min_output_tokens': shared.MIN_OUTPUT,
        'model': 'deepseek-flash', 'thinking': 'enabled', 'reasoning_effort': 'high', 'HTTP_seconds': 300, 'retry': 0,
        'modules': {n: _sha(ROOT / n) for n in names}, 'protocol_sha256': _sha(PROTOCOL),
        'prepared_result_sha256': _sha(PREP / 'result.json'), 'provider_calls': 0,
        'codec_registered_before_call': True, 'full_issue_trusted_not_automatically_promoted': True}


async def call(model, row, phase, evidence, root, ceiling):
    msgs = messages(row['input'], phase, evidence)
    latest = {r['call_id']: r for r in _events(OUT / 'provider_calls.jsonl', RUN_ID)}
    spent = sum(r.get('total_tokens', 0) for r in latest.values() if r['status'] == 'completed' and r['task_id'] == row['instance_id'])
    limit = min(shared.MAX_OUTPUT, shared.TASK - spent - math.ceil(estimate_tokens(_prompt_text(msgs)) * 1.4))
    if limit < shared.MIN_OUTPUT:
        raise ProviderBudgetExceeded('remaining budget cannot reserve >=16k output')
    _save(root / 'request.json', {'messages': [m.model_dump(exclude={'additional_kwargs', 'response_metadata'}) for m in msgs],
        'prompt_sha256': hashlib.sha256(_prompt_text(msgs).encode()).hexdigest(), 'output_limit': limit})
    response = await budgeted_ainvoke(model, msgs, {'configurable': {
        'provider_ledger_path': str(OUT / 'provider_calls.jsonl'), 'provider_run_id': RUN_ID,
        'provider_task_id': row['instance_id'], 'provider_total_token_ceiling': ceiling,
        'provider_task_token_ceiling': shared.TASK, 'provider_max_calls_per_task': 2,
        'provider_max_output_tokens': limit, 'provider_prompt_reserve_multiplier': 1.4,
        'provider_disable_thinking': False}}, role='pair_v2_' + phase)
    record = shared.response_record(response)
    record.update({k: response.response_metadata.get(k) for k in ('reasoning_tokens_reported',
        'reasoning_content_present', 'wire_thinking', 'wire_effort', 'wire_max_tokens', 'HTTP_seconds')})
    _save(root / 'response.json', record)
    if record['response_status'] != 'received':
        raise ValueError('incomplete response; no retry')
    if phase == 'repair':
        canonical, removed = canonical_response(record['raw'])
        _save(root / 'canonical.json', {'raw': canonical, 'known_envelope_removed': removed, 'code_strings_changed': False})
        return canonical
    return record['raw']


async def run():
    frozen = shared.edits._read(OUT / 'freeze.json')
    if frozen != preflight():
        raise ValueError('whole v2 method or inputs changed')
    if (OUT / 'started.json').exists() or (OUT / 'provider_calls.jsonl').exists():
        raise FileExistsError('v2 paid experiment started; no retry')
    tasks = selected_rows()
    if [hashlib.sha256(_prompt_text(messages(r['input'], 'probe')).encode()).hexdigest() for r in tasks] != [
            r['initial_prompt_sha256'] for r in frozen['tasks']]:
        raise ValueError('actual first messages differ from freeze')
    shared.require_engine(tuple(r['image_id'] for r in tasks))
    import httpx

    from core.settings import settings
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError('Flash credential unavailable')
    _save(OUT / 'started.json', {'run_id': RUN_ID, 'no_retry': True})
    async with httpx.AsyncClient(trust_env=False, timeout=300) as client:
        model = shared.FreshFlash(model='deepseek-flash', openai_api_base='https://api.deepseek.com',
            openai_api_key=settings.DEEPSEEK_API_KEY, max_retries=0, streaming=False, http_async_client=client).bind(
                response_format={'type': 'json_object'}, extra_body={'thinking': {'type': 'enabled'}}, reasoning_effort='high')
        try:
            for n, row in enumerate(tasks):
                iid, view, root = row['instance_id'], row['input'], OUT / row['instance_id']
                _save(root / 'input.json', view)
                result = {'instance_id': iid, 'patch_written': False, 'full_issue_trusted': False,
                          'operational_pair_valid': False, 'status': 'not_repaired'}
                try:
                    ceiling = shared.TOTAL - (len(tasks) - n - 1) * shared.TASK
                    candidates = validate_pair(await call(model, row, 'probe', None, root / 'probe-call', ceiling), view, SOURCE / iid)
                    for phase, candidate in candidates.items():
                        _save(root / (phase + '-candidate.json'), candidate)
                    normal = shared.run_probe(candidates['normal'], row, root / 'base-normal')
                    target = shared.run_probe(candidates['target'], row, root / 'base-target')
                    result['operational_pair_valid'] = shared.paired_gate(normal, target)
                    result['status'] = 'pair_execution_gate_not_met'
                    if result['operational_pair_valid']:
                        evidence = {'normal_source': candidates['normal']['source'], 'target_source': candidates['target']['source'],
                            'public_issue_quote': candidates['target']['issue_quote'], 'normal': normal, 'target': target,
                            'operational_candidate_not_semantic_certificate': True}
                        raw = await call(model, row, 'repair', evidence, root / 'repair-call', ceiling)
                        patch = shared.edits.compile_patch(raw, {'production_windows': view['windows'],
                            'base_commit': view['base_commit'], 'allowed_production_paths': view['candidate_paths']}, SOURCE / iid)
                        (root / 'candidate.patch').write_bytes(patch.encode())
                        result.update(patch_written=bool(patch), status='candidate_for_independent_score' if patch else 'abstained')
                        if patch:
                            post = [shared.run_probe(candidates[phase], row, root / ('patch-' + phase), root / 'candidate.patch')
                                for phase in ('normal', 'target')]
                            result['own_post_patch_pass'] = all(r['returncode'] == 0 for v in post for r in v['runs'])
                except (ValueError, TypeError, SyntaxError, PermissionError, ProviderBudgetExceeded) as exc:
                    result.update(status='generation_or_budget_rejected', error_type=type(exc).__name__)
                _save(root / 'generation.json', result)
                print(json.dumps(result), flush=True)
        except Exception as exc:
            _save(OUT / 'failure.json', {'error_type': type(exc).__name__, 'no_retry': True})
            raise
    _save(OUT / 'generation-seal.json', {'files': {p.relative_to(OUT).as_posix(): _sha(p)
        for p in OUT.rglob('*') if p.is_file()}, 'official_scoring_not_started': True})
    seal = shared.edits._read(OUT / 'generation-seal.json')
    if any(_sha(OUT / p) != h for p, h in seal['files'].items()) or frozen != preflight():
        raise ValueError('sealed method changed before independent scoring')
    shared.require_engine(tuple(r['image_id'] for r in tasks))
    official = [shared.grade_one(row, OUT / row['instance_id']) for row in tasks]
    for result in official:
        result['classification'] = ('infrastructure_error' if result.get('timed_out') or result.get('returncode') in {90, 91, 125, 126, 127}
            else 'resolved' if result['resolved'] else 'unresolved' if result.get('official_scoring_attempted') else 'not_attempted')
    result = {'fixed_tasks': len(tasks), 'rows': official, 'full_issue_trusted': False,
              'independent_generalization_claimed': False, 'official_feedback_sent_to_actor': False}
    _save(OUT / 'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'preflight', 'run'))
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare()
    elif args.command == 'preflight':
        result = preflight()
        if (OUT / 'freeze.json').exists():
            if shared.edits._read(OUT / 'freeze.json') != result:
                raise ValueError('existing freeze differs; do not overwrite')
        else:
            _save(OUT / 'freeze.json', result)
    else:
        result = asyncio.run(run())
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
