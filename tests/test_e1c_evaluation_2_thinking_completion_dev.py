import asyncio
import json

import httpx
import pytest
from langchain_core.messages import HumanMessage

from agents.model_budget import budgeted_ainvoke
from evals import e1c_evaluation_2_thinking_completion_dev as method
from evals import e1c_evaluation_2_three_arm_dev as parent


def counts():
    return {'fixed_tasks': 1, 'fixed_cells': 1, 'instance_id': 'old-dev', 'cells': [{'arm': 'strict_evidence'}]}, {
        'fixed_tasks': 1, 'fixed_cells': 3, 'rows': [{'arm': 'strict_evidence', 'instance_id': 'old-dev',
                                                   'generation_status': 'candidate_rejected', 'resolved': False}]}


def test_cardinality_audit_uses_freeze_does_not_mutate_legacy_raw():
    frozen, raw = counts()
    corrected = method.verified_counts(frozen, raw)
    assert corrected['fixed_cells'] == 1 and corrected['raw_reported_fixed_cells'] == 3
    assert corrected['legacy_cardinality_consistent'] is False and corrected['official_candidate_containers'] == 0
    assert raw['fixed_cells'] == 3


@pytest.mark.parametrize('kind', ['missing', 'wrong_arm', 'wrong_task', 'duplicate'])
def test_cardinality_audit_rejects_wrong_or_incomplete_actual_rows(kind):
    frozen, raw = counts()
    if kind == 'missing':
        raw['rows'] = []
    elif kind == 'wrong_arm':
        raw['rows'][0]['arm'] = 'standard'
    elif kind == 'wrong_task':
        raw['rows'][0]['instance_id'] = 'other'
    else:
        raw['rows'].append(dict(raw['rows'][0]))
    with pytest.raises(ValueError, match='frozen cohort'):
        method.verified_counts(frozen, raw)


def test_completion_sdk_wire_and_timeout_are_bounded_offline(tmp_path):
    calls = []

    def handler(request):
        body = json.loads(request.content)
        assert body['model'] == 'deepseek-flash' and body['thinking'] == {'type': 'enabled'}
        assert body['reasoning_effort'] == 'high' and body['max_tokens'] == 24_000
        assert request.extensions['timeout']['read'] == 300
        calls.append(body)
        return httpx.Response(200, json={'id': 'fixture', 'created': 1, 'object': 'chat.completion', 'model': 'deepseek-flash',
            'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '{"edits":[]}',
                                              'reasoning_content': 'fixture'}, 'finish_reason': 'stop'}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 20, 'total_tokens': 30,
                      'completion_tokens_details': {'reasoning_tokens': 15}}})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False, timeout=120) as client:
            model = method.CompletionFlash(model='deepseek-flash', openai_api_key='fixture-key',
                openai_api_base='https://example.invalid', max_retries=0, http_async_client=client).bind(
                    response_format={'type': 'json_object'}, extra_body={'thinking': {'type': 'enabled'}}, reasoning_effort='high')
            with method.configured():
                response = await budgeted_ainvoke(model, [HumanMessage(content='JSON public source')], {'configurable': {
                    'provider_ledger_path': str(tmp_path / 'ledger.jsonl'), 'provider_run_id': 'fixture',
                    'provider_task_id': 'strict', 'provider_total_token_ceiling': 40_000,
                    'provider_task_token_ceiling': 40_000, 'provider_max_calls_per_task': 1,
                    'provider_max_output_tokens': 24_000, 'provider_disable_thinking': False}}, role='fixture')
            assert response.response_metadata['request_http_timeout_seconds'] == 300
            assert response.response_metadata['reasoning_tokens_reported'] == 15

    original = (parent.OUT, parent.OUTPUT_TOKENS, method.previous.OUTPUT_TOKENS)
    asyncio.run(run())
    assert len(calls) == 1 and (parent.OUT, parent.OUTPUT_TOKENS, method.previous.OUTPUT_TOKENS) == original
