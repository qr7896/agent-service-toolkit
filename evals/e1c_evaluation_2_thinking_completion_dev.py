"""Bounded completion-window diagnostic, plus immutable single-cell result audit."""

from __future__ import annotations

import argparse
import asyncio
import json
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from evals import e1c_evaluation_2_flash_thinking_dev as previous
from evals import e1c_evaluation_2_three_arm_dev as parent
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

RUN_ID = 'e1c2-flash-thinking-completion-dev-v2'
OUT = ROOT / '.codex/e1c/evaluation_2' / RUN_ID
AUDIT = ROOT / '.codex/e1c/evaluation_2/flash-thinking-cardinality-zero-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_THINKING_COMPLETION_PROTOCOL_2026-10-09.md'
TOTAL_TOKENS, OUTPUT_TOKENS, HTTP_SECONDS = 40_000, 24_000, 300


def verified_counts(frozen, raw):
    expected = [c['arm'] for c in frozen['cells']]
    actual = [r['arm'] for r in raw['rows']]
    if (len(expected) != frozen['fixed_cells'] or actual != expected or len(set(actual)) != len(actual)
            or any(r['instance_id'] != frozen['instance_id'] for r in raw['rows'])):
        raise ValueError('actual rows differ from frozen cohort')
    return {**raw, 'fixed_tasks': frozen['fixed_tasks'], 'fixed_cells': frozen['fixed_cells'],
            'raw_reported_fixed_cells': raw['fixed_cells'],
            'legacy_cardinality_consistent': raw['fixed_cells'] == frozen['fixed_cells'],
            'counts_from_freeze_and_rows_not_rewritten_raw': True,
            'official_candidate_containers': sum(r['generation_status'] == 'candidate' for r in raw['rows'])}


def audit_previous():
    if AUDIT.exists():
        raise FileExistsError('cardinality audit started; no retry')
    with previous.configured():
        frozen = parent._read(previous.OUT / 'freeze.json')
        if frozen != previous.preflight():
            raise ValueError('original thinking identity changed')
        parent.verify_seal(previous.OUT)
    raw = parent._read(previous.OUT / 'result.json')
    corrected = verified_counts(frozen, raw)
    names = ('freeze.json', 'generation-seal.json', 'result.json', 'provider_calls.jsonl')
    bindings = {name: _sha(previous.OUT / name) for name in names}
    _save(AUDIT / 'freeze.json', {'bindings': bindings, 'module_sha256': _sha(ROOT / 'evals/e1c_evaluation_2_thinking_completion_dev.py'),
                                'protocol_sha256': _sha(PROTOCOL), 'provider_calls': 0, 'original_result_not_modified': True})
    _save(AUDIT / 'verified-result.json', corrected)
    if any(_sha(previous.OUT / n) != h for n, h in bindings.items()):
        raise ValueError('original producer files changed')
    return {'provider_calls': 0, 'fixed_cells': corrected['fixed_cells'], 'raw_reported_fixed_cells': raw['fixed_cells'],
            'legacy_cardinality_consistent': corrected['legacy_cardinality_consistent'], 'original_result_not_modified': True}


class CompletionFlash(previous.ThinkingFlash):
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        payload = self._get_request_payload(messages, stop=stop, **kwargs)
        verified = previous.assert_wire(payload)
        raw = await self.async_client.with_raw_response.create(**payload, timeout=HTTP_SECONDS)
        parsed = raw.parse()
        result = self._create_chat_result(parsed)
        details = getattr(parsed.usage, 'completion_tokens_details', None)
        metadata = {'verified_wire_profile': verified, 'request_http_timeout_seconds': HTTP_SECONDS,
                    'reasoning_tokens_reported': getattr(details, 'reasoning_tokens', None),
                    'reasoning_content_present': bool(getattr(parsed.choices[0].message, 'reasoning_content', None))}
        result.generations[0].message.response_metadata.update(metadata)
        result.llm_output = {**(result.llm_output or {}), **metadata}
        return result


def response_record(response):
    return {**previous.response_record(response),
            'request_http_timeout_seconds': (response.response_metadata or {}).get('request_http_timeout_seconds')}


def preflight():
    old = parent._read(previous.OUT / 'freeze.json')
    value = previous.preflight()
    if value['cells'][0]['prompt_sha256'] != old['cells'][0]['prompt_sha256']:
        raise ValueError('thinking diagnostic prompt changed')
    return {**value, 'schema': 'e1c2-thinking-completion-dev-v2',
            'completion_module_sha256': _sha(ROOT / 'evals/e1c_evaluation_2_thinking_completion_dev.py'),
            'previous_thinking_seal_sha256': _sha(previous.OUT / 'generation-seal.json'),
            'HTTP_timeout_seconds': HTTP_SECONDS, 'previous_8k_result_censored_not_repair_failure': True,
            'same_prompt_mode_effort': True, 'output_and_total_and_http_budget_changed': True,
            'verified_result_cardinality_from_freeze': True}


@contextmanager
def configured():
    with previous.configured(), ExitStack() as stack:
        stack.enter_context(patch.object(previous, 'OUTPUT_TOKENS', OUTPUT_TOKENS))
        for name, value in {'RUN_ID': RUN_ID, 'OUT': OUT, 'PROTOCOL': PROTOCOL,
                            'TOTAL_TOKENS': TOTAL_TOKENS, 'CELL_TOKENS': TOTAL_TOKENS,
                            'OUTPUT_TOKENS': OUTPUT_TOKENS, 'RawJsonFlash': CompletionFlash,
                            'preflight': preflight, 'response_record': response_record}.items():
            stack.enter_context(patch.object(parent, name, value))
        yield


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('audit-previous', 'preflight', 'run'))
    args = parser.parse_args()
    if args.command == 'audit-previous':
        print(json.dumps(audit_previous()), flush=True)
        return
    with configured():
        if args.command == 'preflight':
            frozen = preflight()
            if (OUT / 'freeze.json').exists():
                if parent._read(OUT / 'freeze.json') != frozen:
                    raise ValueError('existing completion freeze differs; do not overwrite')
            else:
                _save(OUT / 'freeze.json', frozen)
            print(json.dumps({'ready': True, 'cells': frozen['cells'], 'max_calls': 1,
                              'max_provider_tokens': TOTAL_TOKENS, 'provider_calls': 0}), flush=True)
        else:
            asyncio.run(parent.generate())
            raw = parent.grade()  # Preserve legacy scorer output separately, never silently rewrite it.
            corrected = verified_counts(parent._read(OUT / 'freeze.json'), raw)
            _save(OUT / 'verified-result.json', corrected)
            print(json.dumps(corrected), flush=True)


if __name__ == '__main__':
    main()
