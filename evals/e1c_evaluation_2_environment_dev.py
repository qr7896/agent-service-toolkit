"""OLD DEV: feed actual enforced conditions back without upgrading qualification."""

from __future__ import annotations

import argparse
import asyncio
import json
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from evals import e1c_evaluation_2_protocol_guard_dev as previous
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_environment_feedback import project_environment

PARENT = previous.OUT
PARENT_PROTOCOL = previous.PROTOCOL
OUT = ROOT / '.codex/e1c/evaluation_2/environment-feedback-flash-dev-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_ENVIRONMENT_DEV_2026-10-08.md'
MODULES = (*previous.MODULES, 'evals/e1c_evaluation_2_environment_feedback.py', 'evals/e1c_evaluation_2_environment_dev.py')
POLICY = previous.POLICY + (
    ' An explicit public request to add/expose a parameter is different from an existing supported API. '
    'When the base signature lacks that exact requested parameter, a target constructor with the publicly '
    'requested argument is a legitimate failing entrypoint, not a fabricated API. The normal control must '
    'use a separate receiver with source-supported arguments. Do not put unsupported construction in shared '
    'setup. Keyword acceptance proves only that sub-obligation, not defaults or full functionality. '
    'own_executor_environment describes an actually enforced import-failure condition shared by control '
    'and target; do not ignore it or assume natural uninstallation. It does not prove semantic alignment. '
    'After automatic dependency acquisition, inspect the new source and use remaining turns to produce '
    'a faithful probe, or explicitly identify a different unresolved obligation. Preserve all public inputs.'
)


def checked_parent():
    frozen = json.loads((PARENT / 'freeze.json').read_bytes())
    seal = json.loads((PARENT / 'generation-seal.json').read_bytes())
    if (any(_sha(ROOT / name) != digest for name, digest in frozen['method_sha256'].items())
            or frozen['protocol_sha256'] != _sha(PARENT_PROTOCOL)
            or any(_sha(PARENT / name) != digest for name, digest in seal['files'].items())
            or json.loads((PARENT / 'state.json').read_bytes())['status'] != 'completed'):
        raise ValueError('completed frozen parent changed')


def annotate(result, root):
    feedback, oracle, candidate, execution = result
    if execution is None or execution.get('missing_optional_import') is None:
        return result
    controls = [json.loads((root / f'control-{n}.json').read_bytes()) for n in (1, 2)]
    projected = project_environment(feedback, controls, execution)
    _save(root / 'environment-feedback.json', projected['own_executor_environment'])
    return projected, oracle, candidate, execution


def preflight():
    checked_parent()
    return {**previous.preflight(), 'schema': 'e1c2-environment-feedback-flash-dev-v1',
            'matching_enforced_condition_in_next_model_feedback': True,
            'explicit_public_change_request_target_allowed': True,
            'qualification_not_upgraded_by_environment': True, 'parent_seal_sha256': _sha(PARENT / 'generation-seal.json'),
            'actual_message_zero_gate_sha256': _sha(OUT / 'message-check.json')}


@contextmanager
def configured():
    with ExitStack() as stack:
        for key, value in [('OUT', OUT), ('PROTOCOL', PROTOCOL), ('MODULES', MODULES), ('POLICY', POLICY)]:
            stack.enter_context(patch.object(previous, key, value))
        compiled = stack.enter_context(previous.configured())
        original_configured = compiled.configured

        @contextmanager
        def environment_hooks():
            with original_configured():
                execute = compiled.base.loop.execute_probe

                def with_environment(payload, frozen, workspace, image, root, environment, locked=None):
                    return annotate(execute(payload, frozen, workspace, image, root, environment, locked), root)

                with patch.object(compiled.base.loop, 'execute_probe', with_environment):
                    yield

        stack.enter_context(patch.object(compiled, 'configured', environment_hooks))
        stack.enter_context(patch.object(compiled, 'preflight', preflight))
        yield compiled


def freeze():
    with configured() as compiled:
        checked_parent()
        previous.preflight()
        # Recompose actual final messages from every parent environment-bearing probe, without executing it.
        with compiled.configured():
            compiled.inputs()
            rows = []
            for path in sorted(PARENT.glob('*/turn-*/execution.json')):
                execution = json.loads(path.read_bytes())
                if execution.get('missing_optional_import') is None:
                    continue
                root = path.parent
                feedback = json.loads((root / 'feedback.json').read_bytes())
                initial = json.loads((root / 'input.json').read_bytes())
                with patch(__name__ + '._save', lambda *args: None):
                    projected, _, _, _ = annotate((feedback, None, None, execution), root)
                messages = compiled.conversation(compiled.base.loop.messages(initial, projected), 3)
                body = json.loads(messages[1].content)
                actual = body['last_feedback']['own_executor_environment']
                if actual != projected['own_executor_environment'] or messages[0].content != POLICY:
                    raise ValueError('environment/policy absent from actual final messages')
                rows.append({'source': path.relative_to(PARENT).as_posix(), 'module': actual['module'],
                             'actual_next_message_contains_enforced_condition': True, 'provider_calls': 0})
            if not rows:
                raise ValueError('actual parent environment regression required')
        _save(OUT / 'message-check.json', rows)
        value = preflight()
        _save(OUT / 'freeze.json', value)
    return {k: value[k] for k in ('schema', 'model', 'max_provider_calls', 'batch_token_cap', 'task_token_cap', 'max_retries')}


async def run():
    with configured() as compiled:
        if not (OUT / 'message-check.json').is_file():
            raise ValueError('final-message zero gate absent')
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
