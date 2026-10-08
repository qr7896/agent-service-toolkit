"""Bounded production module.function hints in the actual OLD DEV retrieval hook."""

from __future__ import annotations

import argparse
import asyncio
import json
from contextlib import ExitStack, contextmanager
from pathlib import PurePosixPath
from unittest.mock import patch

from evals import e1c_evaluation_2_environment_dev as previous
from evals.e1c_evaluation_2_bounded_repro_loop import retrieve as original_retrieve
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

PARENT, PARENT_PROTOCOL = previous.OUT, previous.PROTOCOL
OUT = ROOT / '.codex/e1c/evaluation_2/module-retrieval-flash-dev-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_MODULE_RETRIEVAL_DEV_2026-10-08.md'
MODULES = (*previous.MODULES, 'evals/e1c_evaluation_2_module_retrieval_dev.py')
_preflight = previous.preflight


def retrieve(query, workspace):
    rows, feedback = original_retrieve(query, workspace)
    if rows or '.' not in query or feedback['scan_budget_exhausted']:
        return rows, feedback
    module, name = query.split('.')
    candidates, fallback = original_retrieve(name, workspace)
    # A basename is only a retrieval hint, never a public alias/namespace certificate.
    rows = [{**row, 'origin': 'agent_module_name_hint', 'alias_binding_proven': False} for row in candidates
            if PurePosixPath(row['path']).stem == module and row['text'].startswith(('def ', 'async def '))]
    return rows, {**feedback, 'matches': len(rows), 'module_name_hint': module, 'alias_binding_proven': False,
                  'scan_bytes': feedback['scan_bytes'] + fallback['scan_bytes'],
                  'scan_budget_exhausted': fallback['scan_budget_exhausted'], 'fallback_plain_symbol': name}


def preflight():
    frozen = json.loads((PARENT / 'freeze.json').read_bytes())
    seal = json.loads((PARENT / 'generation-seal.json').read_bytes())
    if (any(_sha(ROOT / name) != digest for name, digest in frozen['method_sha256'].items())
            or frozen['protocol_sha256'] != _sha(PARENT_PROTOCOL)
            or any(_sha(PARENT / name) != digest for name, digest in seal['files'].items())):
        raise ValueError('parent producer identity changed')
    return {**_preflight(), 'schema': 'e1c2-module-retrieval-flash-dev-v1',
            'dotted_module_function_hint': True, 'alias_binding_not_inferred': True,
            'retrieval_scan_limit_bytes': 64 * 1024 * 1024, 'parent_environment_trial_seal_sha256': _sha(PARENT / 'generation-seal.json'),
            'retrieval_zero_gate_sha256': _sha(OUT / 'retrieval-check.json')}


@contextmanager
def configured():
    with ExitStack() as stack:
        for key, value in [('OUT', OUT), ('PROTOCOL', PROTOCOL), ('MODULES', MODULES)]:
            stack.enter_context(patch.object(previous, key, value))
        compiled = stack.enter_context(previous.configured())
        original = compiled.configured

        @contextmanager
        def retrieval_hooks():
            with original(), patch.object(compiled.base.loop, 'retrieve', retrieve):
                yield

        stack.enter_context(patch.object(compiled, 'configured', retrieval_hooks))
        stack.enter_context(patch.object(compiled, 'preflight', preflight))
        yield compiled


def freeze():
    with configured() as compiled, compiled.configured():
        _save(OUT / 'message-check.json', json.loads((PARENT / 'message-check.json').read_bytes()))
        checks = []
        for task, initial, workspace in compiled.inputs():
            for path in sorted((PARENT / task['instance_id']).glob('turn-*/response.json')):
                raw = json.loads(path.read_bytes())['raw']
                action, query, _ = previous.previous.stage.pilot.protocol.decode(raw, initial['issue'])
                if action != 'retrieve' or '.' not in query:
                    continue
                rows, feedback = compiled.base.loop.retrieve(query, workspace)
                if rows and feedback.get('fallback_plain_symbol'):
                    visible = compiled.base.loop.enrich(initial, rows)
                    body = json.loads(compiled.base.loop.messages(visible, feedback)[1].content)
                    if not any(w['path'] == rows[0]['path'] and w['start_line'] == rows[0]['start_line'] for w in body['windows']):
                        raise ValueError('actual retrieved definition absent from final Human')
                    checks.append({'query': query, 'path': rows[0]['path'], 'source_sha256': rows[0]['source_sha256'],
                                   'actual_next_message_contains_definition': True, 'alias_binding_proven': False, 'provider_calls': 0})
        if not checks:
            raise ValueError('actual previous failed module query regression required')
        _save(OUT / 'retrieval-check.json', checks)
        value = preflight()
        _save(OUT / 'freeze.json', value)
    return {k: value[k] for k in ('schema', 'model', 'max_provider_calls', 'batch_token_cap', 'task_token_cap', 'max_retries')}


async def run():
    with configured() as compiled:
        return await compiled.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('freeze', 'run', 'gold'))
    args = parser.parse_args()
    if args.command == 'gold':
        with configured() as compiled:
            value = compiled.grade()
    else:
        value = asyncio.run(run()) if args.command == 'run' else freeze()
    print(json.dumps(value, ensure_ascii=False), flush=True)
