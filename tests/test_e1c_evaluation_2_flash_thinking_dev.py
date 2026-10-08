import asyncio
import json

import httpx
import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from agents.model_budget import budgeted_ainvoke
from evals import e1c_evaluation_2_flash_thinking_dev as profile
from evals import e1c_evaluation_2_three_arm_dev as parent


def wire():
    return {'model': 'deepseek-flash', 'response_format': {'type': 'json_object'},
            'reasoning_effort': 'high', 'extra_body': {'thinking': {'type': 'enabled'}, 'max_tokens': 8000}}


@pytest.mark.parametrize('change', [lambda p: p.update(model='deepseek-v4-pro'),
                                  lambda p: p['extra_body'].update(thinking={'type': 'disabled'}),
                                  lambda p: p['extra_body'].update(max_tokens=64_000),
                                  lambda p: p.update(reasoning_effort='max'),
                                  lambda p: p.update(tools=[{'unapproved': True}])])
def test_actual_request_guard_rejects_wrong_model_mode_budget_effort_or_tools(change):
    payload = wire()
    change(payload)
    with pytest.raises(ValueError, match='actual SDK request'):
        profile.assert_wire(payload)


def test_sdk_http_body_and_gateway_include_reasoning_usage_offline(tmp_path, monkeypatch):
    calls = []

    def handler(request):
        payload = json.loads(request.content)
        assert payload['thinking'] == {'type': 'enabled'}
        assert payload['reasoning_effort'] == 'high' and payload['max_tokens'] == 8000
        assert payload['model'] == 'deepseek-flash' and payload['response_format'] == {'type': 'json_object'}
        calls.append(payload)
        return httpx.Response(200, json={
            'id': 'fixture', 'created': 1, 'object': 'chat.completion', 'model': 'deepseek-flash',
            'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '{"edits":[]}',
                                              'reasoning_content': 'fixture reasoning'}, 'finish_reason': 'stop'}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 20, 'total_tokens': 30,
                      'completion_tokens_details': {'reasoning_tokens': 15}}})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as client:
            model = profile.ThinkingFlash(model='deepseek-flash', openai_api_key='fixture-key',
                                          openai_api_base='https://example.invalid', max_retries=0,
                                          http_async_client=client).bind(response_format={'type': 'json_object'})
            monkeypatch.setattr(profile, '_invoke', budgeted_ainvoke)
            response = await profile.invoke(model, [SystemMessage(content='Return JSON edits'), HumanMessage(content='public source')],
                {'configurable': {'provider_ledger_path': str(tmp_path / 'ledger.jsonl'), 'provider_run_id': 'fixture',
                                  'provider_task_id': 'strict', 'provider_total_token_ceiling': 30_000,
                                  'provider_task_token_ceiling': 30_000, 'provider_max_calls_per_task': 1,
                                  'provider_max_output_tokens': 8000, 'provider_disable_thinking': True}}, role='fixture')
            record = profile.response_record(response)
            assert record['verified_wire_profile']['thinking'] == 'enabled'
            assert record['reasoning_tokens_reported'] == 15 and record['reasoning_content_present'] is True
            assert 'fixture reasoning' not in json.dumps(record)
            assert record['usage']['total_tokens'] == 30

    asyncio.run(run())
    ledger = [json.loads(line) for line in (tmp_path / 'ledger.jsonl').read_text().splitlines()]
    assert len(calls) == 1 and ledger[-1]['total_tokens'] == 30 and ledger[-1]['status'] == 'completed'


def test_one_cell_configuration_restores_original_budget_and_model_hook():
    original = (parent.OUT, parent.ARMS, parent.TOTAL_TOKENS, parent.RawJsonFlash, parent.budgeted_ainvoke)
    with profile.configured():
        assert parent.ARMS == ('strict_evidence',) and parent.TOTAL_TOKENS == 30_000
        assert parent.OUTPUT_TOKENS == 8000 and parent.RawJsonFlash is profile.ThinkingFlash
        assert parent.budgeted_ainvoke is profile.invoke
    assert (parent.OUT, parent.ARMS, parent.TOTAL_TOKENS, parent.RawJsonFlash, parent.budgeted_ainvoke) == original


def test_legacy_three_payload_preflight_freezes_only_same_strict_cell(monkeypatch):
    cells = [{'arm': a, 'prompt_sha256': a + '-hash'} for a in profile._arms]
    monkeypatch.setattr(parent, '_read', lambda _: {'cells': cells})
    monkeypatch.setattr(parent, 'verify_seal', lambda _: parent.ARMS == profile._arms or pytest.fail('wrong parent seal arm identity'))
    monkeypatch.setattr(profile, '_sha', lambda _: 'fixture-hash')
    monkeypatch.setattr(profile.boundary, 'preflight', lambda: {'cells': cells})
    frozen = profile.preflight()
    assert frozen['fixed_cells'] == 1 and frozen['max_provider_calls'] == 1
    assert frozen['cells'] == [cells[2]] and frozen['same_v2_strict_prompt'] is True
    assert frozen['prepared_but_not_sent_arms'] == ['standard', 'standard_evidence']
