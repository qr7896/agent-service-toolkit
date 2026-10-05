"""Use the basic completion endpoint so truncated JSON retains content and usage."""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from evals.e1b_editor_adapter import content_text, usage_tokens


class RawJsonFlash(ChatOpenAI):
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        if self.model_name != "deepseek-flash":
            raise ValueError("this adapter is frozen to deepseek-flash")
        payload = self._get_request_payload(messages, stop=stop, **kwargs)
        raw = await self.async_client.with_raw_response.create(**payload)
        return self._create_chat_result(raw.parse())


def response_record(response) -> dict:
    metadata = response.response_metadata or {}
    raw = content_text(response)
    reason = metadata.get("finish_reason")
    return {"raw": raw, "usage": usage_tokens(response), "finish_reason": reason,
            "provider_model": metadata.get("model_name"),
            "response_status": "truncated" if reason == "length" else "empty" if not raw.strip() else "received"}
