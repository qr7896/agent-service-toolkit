"""Optional fail-closed provider-token guard for budgeted experiment runs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from langchain_core.messages import ToolMessage

from agents.model_router import estimate_tokens
from agents.trajectory import utc_now


class ProviderBudgetExceeded(RuntimeError):
    pass


class AmbiguousProviderCall(RuntimeError):
    pass


def _conf(config: Any) -> dict[str, Any]:
    return (config or {}).get("configurable") or {}


def _append(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def _events(path: Path, run_id: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("run_id") == run_id:
            rows.append(row)
    return rows


def _usage(response: Any) -> dict[str, int]:
    usage = dict(getattr(response, "usage_metadata", None) or {})
    metadata = dict(getattr(response, "response_metadata", None) or {})
    token_usage = dict(metadata.get("token_usage") or metadata.get("usage") or {})
    input_tokens = int(usage.get("input_tokens") or token_usage.get("prompt_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or token_usage.get("completion_tokens") or 0)
    total_tokens = int(
        usage.get("total_tokens") or token_usage.get("total_tokens") or input_tokens + output_tokens
    )
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def _prompt_text(messages: list[Any]) -> str:
    return json.dumps(
        [
            {
                "type": message.__class__.__name__,
                "content": str(getattr(message, "content", "") or ""),
                "tool_calls": getattr(message, "tool_calls", None) or [],
            }
            for message in messages
        ],
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )


def _bounded_messages(messages: list[Any], max_tool_result_chars: int) -> list[Any]:
    bounded = []
    for message in messages:
        content = getattr(message, "content", "")
        if (
            isinstance(message, ToolMessage)
            and isinstance(content, str)
            and max_tool_result_chars > 0
            and len(content) > max_tool_result_chars
        ):
            suffix = f"\n...[tool output truncated from {len(content)} chars]"
            bounded.append(
                message.model_copy(
                    update={"content": content[: max_tool_result_chars - len(suffix)] + suffix}
                )
            )
        else:
            bounded.append(message)
    return bounded


def _status_code(exc: Exception) -> int | None:
    value = getattr(exc, "status_code", None)
    if value is None:
        value = getattr(getattr(exc, "response", None), "status_code", None)
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


async def budgeted_ainvoke(
    model: Any,
    messages: list[Any],
    config: Any,
    *,
    role: str,
) -> Any:
    """Invoke normally unless a provider ledger is configured."""
    conf = _conf(config)
    ledger_value = conf.get("provider_ledger_path")
    if not ledger_value:
        return await model.ainvoke(messages)

    ledger = Path(str(ledger_value))
    run_id = str(conf.get("provider_run_id") or "")
    task_id = str(conf.get("provider_task_id") or "")
    if not run_id or not task_id:
        raise ValueError("provider_run_id and provider_task_id are required")

    rows = _events(ledger, run_id)
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        latest[str(row.get("call_id") or "")] = row
    unresolved = [
        call_id for call_id, row in latest.items() if row.get("status") in {"started", "ambiguous"}
    ]
    if unresolved:
        raise AmbiguousProviderCall(f"unresolved provider calls: {sorted(unresolved)}")

    completed = [row for row in latest.values() if row.get("status") == "completed"]
    global_spent = sum(int(row.get("total_tokens") or 0) for row in completed)
    task_completed = [row for row in completed if row.get("task_id") == task_id]
    task_spent = sum(int(row.get("total_tokens") or 0) for row in task_completed)
    max_calls = int(conf.get("provider_max_calls_per_task") or 0)
    if max_calls and len(task_completed) >= max_calls:
        raise ProviderBudgetExceeded(
            f"task call ceiling reached: {len(task_completed)}/{max_calls}"
        )

    max_output = int(conf.get("provider_max_output_tokens") or 600)
    bounded_messages = _bounded_messages(
        messages, int(conf.get("provider_max_tool_result_chars") or 12_000)
    )
    prompt = _prompt_text(bounded_messages)
    reserve = max(
        int(conf.get("provider_min_call_reserve") or 0),
        estimate_tokens(prompt) + max_output,
    )
    global_ceiling = int(conf.get("provider_total_token_ceiling") or 0)
    task_ceiling = int(conf.get("provider_task_token_ceiling") or 0)
    if global_ceiling and global_spent + reserve > global_ceiling:
        raise ProviderBudgetExceeded(
            f"global reserve does not fit: spent={global_spent}, reserve={reserve}, "
            f"ceiling={global_ceiling}"
        )
    if task_ceiling and task_spent + reserve > task_ceiling:
        raise ProviderBudgetExceeded(
            f"task reserve does not fit: spent={task_spent}, reserve={reserve}, "
            f"ceiling={task_ceiling}"
        )

    call_id = str(uuid4())
    common = {
        "protocol": "v3-provider-call-ledger-v1",
        "run_id": run_id,
        "task_id": task_id,
        "call_id": call_id,
        "role": role,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
    }
    _append(ledger, {**common, "status": "started", "event_time": utc_now(), "reserve": reserve})

    bound = model.bind(temperature=0, max_tokens=max_output)
    if conf.get("provider_disable_thinking", False):
        bound = bound.bind(extra_body={"thinking": {"type": "disabled"}})
    try:
        response = await bound.ainvoke(bounded_messages)
    except Exception as exc:
        status_code = _status_code(exc)
        status = "failed" if status_code is not None else "ambiguous"
        _append(
            ledger,
            {
                **common,
                "status": status,
                "event_time": utc_now(),
                "status_code": status_code,
                "error_type": type(exc).__name__,
            },
        )
        raise

    usage = _usage(response)
    if usage["total_tokens"] <= 0:
        _append(
            ledger,
            {**common, "status": "ambiguous", "event_time": utc_now(), "reason": "missing_usage"},
        )
        raise AmbiguousProviderCall("provider response had no token usage")
    _append(
        ledger,
        {
            **common,
            "status": "completed",
            "event_time": utc_now(),
            **usage,
            "response_model": str(
                (getattr(response, "response_metadata", None) or {}).get("model_name") or ""
            ),
        },
    )
    return response


__all__ = [
    "AmbiguousProviderCall",
    "ProviderBudgetExceeded",
    "budgeted_ainvoke",
]
