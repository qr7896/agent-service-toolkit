"""One strict OLD DEV cell: same v2 prompt, explicit Flash thinking and bounded output."""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from evals import e1c_evaluation_2_three_arm_boundary_dev as boundary
from evals import e1c_evaluation_2_three_arm_dev as parent
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_raw_json import RawJsonFlash

RUN_ID = 'e1c2-flash-thinking-strict-dev-v1'
OUT = ROOT / '.codex/e1c/evaluation_2' / RUN_ID
PROTOCOL = ROOT / 'docs/research/E1C2_FLASH_THINKING_DEV_PROTOCOL_2026-10-08.md'
TOTAL_TOKENS, OUTPUT_TOKENS = 30_000, 8_000
_invoke, _arms = parent.budgeted_ainvoke, parent.ARMS


def assert_wire(payload):
    extra = payload.get('extra_body') or {}
    if (payload.get('model') != 'deepseek-flash' or extra.get('thinking') != {'type': 'enabled'}
            or payload.get('reasoning_effort') != 'high' or extra.get('max_tokens') != OUTPUT_TOKENS
            or payload.get('response_format') != {'type': 'json_object'} or payload.get('tools')):
        raise ValueError('actual SDK request differs from frozen Flash thinking profile')
    return {'model': payload['model'], 'thinking': 'enabled', 'reasoning_effort': 'high',
            'max_generated_tokens_including_reasoning': OUTPUT_TOKENS, 'tools_sent': False}


class ThinkingFlash(RawJsonFlash):
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        payload = self._get_request_payload(messages, stop=stop, **kwargs)
        verified = assert_wire(payload)  # Fail before HTTP; no credential or message content logged.
        raw = await self.async_client.with_raw_response.create(**payload)
        parsed = raw.parse()
        result = self._create_chat_result(parsed)
        details = getattr(parsed.usage, 'completion_tokens_details', None)
        metadata = {'verified_wire_profile': verified,
                    'reasoning_tokens_reported': getattr(details, 'reasoning_tokens', None),
                    'reasoning_content_present': bool(getattr(parsed.choices[0].message, 'reasoning_content', None))}
        result.generations[0].message.response_metadata.update(metadata)
        result.llm_output = {**(result.llm_output or {}), **metadata}
        return result


async def invoke(model, messages, config, *, role):
    config = copy.deepcopy(config)
    config['configurable']['provider_disable_thinking'] = False
    model = model.bind(extra_body={'thinking': {'type': 'enabled'}}, reasoning_effort='high')
    return await _invoke(model, messages, config, role=role)


def inputs():
    # Preparation remains shared with v2; it reads base tests for standard arms,
    # Legacy preflight requires all three prepared payloads; the generator loop
    # is restricted to the strict arm, so the other two are never sent.
    with patch.object(parent, 'ARMS', _arms):
        task, bodies, bindings = boundary.inputs()
    return task, bodies, bindings


def response_record(response):
    record = boundary.response_record(response)
    metadata = response.response_metadata or {}
    return {**record, **{k: metadata.get(k) for k in
            ('verified_wire_profile', 'reasoning_tokens_reported', 'reasoning_content_present')}}


def preflight():
    original = parent._read(boundary.OUT / 'freeze.json')
    # Verify the completed v2 producer under its original three-arm identity.
    with patch.object(parent, 'ARMS', _arms):
        parent.verify_seal(boundary.OUT)
    value = boundary.preflight()
    expected = next(c['prompt_sha256'] for c in original['cells'] if c['arm'] == 'strict_evidence')
    selected = [c for c in value['cells'] if c['arm'] == 'strict_evidence']
    if len(selected) != 1 or selected[0]['prompt_sha256'] != expected:
        raise ValueError('strict prompt changed; this is not the preregistered configuration diagnostic')
    return {**value, 'cells': selected, 'schema': 'e1c2-flash-thinking-strict-dev-v1', 'thinking': 'enabled',
            'reasoning_effort': 'high', 'max_provider_calls': 1, 'fixed_cells': 1,
            'thinking_module_sha256': _sha(ROOT / 'evals/e1c_evaluation_2_flash_thinking_dev.py'),
            'parent_v2_seal_sha256': _sha(boundary.OUT / 'generation-seal.json'),
            'same_v2_strict_prompt': True, 'output_and_total_budget_also_changed': True,
            'prepared_but_not_sent_arms': ['standard', 'standard_evidence'],
            'isolated_thinking_causal_effect_claimed': False, 'temperature_effective_in_thinking': False}


@contextmanager
def configured():
    with boundary.configured(), ExitStack() as stack:
        for name, value in {'RUN_ID': RUN_ID, 'OUT': OUT, 'PROTOCOL': PROTOCOL,
                            'ARMS': ('strict_evidence',), 'TOTAL_TOKENS': TOTAL_TOKENS,
                            'CELL_TOKENS': TOTAL_TOKENS, 'OUTPUT_TOKENS': OUTPUT_TOKENS,
                            'RawJsonFlash': ThinkingFlash, 'budgeted_ainvoke': invoke,
                            'inputs': inputs, 'preflight': preflight, 'response_record': response_record}.items():
            stack.enter_context(patch.object(parent, name, value))
        yield


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('preflight', 'run'))
    args = parser.parse_args()
    with configured():
        if args.command == 'preflight':
            frozen = preflight()
            if (OUT / 'freeze.json').exists():
                if parent._read(OUT / 'freeze.json') != frozen:
                    raise ValueError('existing thinking freeze differs; do not overwrite')
            else:
                _save(OUT / 'freeze.json', frozen)
            print(json.dumps({'ready': True, 'cells': frozen['cells'], 'max_calls': 1,
                              'max_provider_tokens': TOTAL_TOKENS, 'provider_calls': 0}), flush=True)
        else:
            asyncio.run(parent.generate())
            print(json.dumps(parent.grade()), flush=True)


if __name__ == '__main__':
    main()
