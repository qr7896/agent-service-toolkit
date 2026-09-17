"""Coding Agent 的可分析执行轨迹（阶段 14）。

轨迹只记录任务执行的必要事实，落盘格式采用一行一条 JSON（JSONL）。这样即使
单条记录损坏，也不会影响其他记录；后续 Evaluation 和 Experience Memory 都能
直接顺序读取它。默认目录 `.codex/trajectories/` 被 git 忽略，避免提交运行数据。
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from agents.code_tools import PROJECT_ROOT

DEFAULT_TRAJECTORY_PATH = PROJECT_ROOT / ".codex" / "trajectories" / "coding_agent.jsonl"
SENSITIVE_KEY_MARKERS = ("api_key", "apikey", "secret", "token", "password", "authorization")


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def human_task(messages: list[Any]) -> str:
    for message in messages:
        if message.__class__.__name__ == "HumanMessage":
            return str(getattr(message, "content", "") or "")
    return ""


_human_task = human_task


def _tool_calls(messages: list[Any]) -> list[dict[str, Any]]:
    """提取模型实际请求的工具，参数只保留键名，避免把文件内容或密钥写入轨迹。"""
    calls: list[dict[str, Any]] = []
    for message in messages:
        for call in getattr(message, "tool_calls", None) or []:
            args = call.get("args") or {}
            calls.append({"name": str(call.get("name") or ""), "arg_keys": sorted(map(str, args))})
    return calls


def _changed_paths(messages: list[Any], approvals: list[dict[str, Any]]) -> list[str]:
    paths = {str(item.get("path")) for item in approvals if item.get("path")}
    # Tool call 参数不落盘，但 path 是后续评测需要的最小可用证据。
    for message in messages:
        for call in getattr(message, "tool_calls", None) or []:
            if call.get("name") in {"write_file", "edit_file"}:
                path = str((call.get("args") or {}).get("path") or "")
                if path:
                    paths.add(path)
    return sorted(paths)


def _status(state: dict[str, Any]) -> str:
    result = state.get("test_result") or {}
    review = state.get("review") or {}
    if result.get("status") == "passed" and review.get("approved") is True:
        return "succeeded"
    if result and result.get("status") != "passed":
        return "failed"
    if review and review.get("approved") is False:
        return "review_rejected"
    return "completed_read_only"


def redact(value: Any, key: str = "") -> Any:
    """递归清除敏感字段，保证轨迹不能意外变成凭据存储。"""
    if any(marker in key.lower() for marker in SENSITIVE_KEY_MARKERS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


# 旧名字保留，避免已发布的调用点失效
_safe = redact


def build_trajectory(state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """从图的最终 State 生成纯 JSON 可序列化的记录，不执行任何 IO。"""
    messages = state.get("messages") or []
    calls = _tool_calls(messages)
    counts = Counter(call["name"] for call in calls)
    ended_at = utc_now()
    started_at = str(state.get("trajectory_started_at") or ended_at)
    try:
        duration_seconds = max(0.0, (datetime.fromisoformat(ended_at) - datetime.fromisoformat(started_at)).total_seconds())
    except ValueError:
        duration_seconds = 0.0
    configurable = config.get("configurable") or {}
    approvals = state.get("approvals") or []
    record = {
        "id": str(uuid4()),
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_seconds": round(duration_seconds, 3),
        "task": _human_task(messages),
        "plan": state.get("plan") or {},
        "tool_calls": calls,
        "tool_call_counts": dict(sorted(counts.items())),
        "changed_paths": _changed_paths(messages, approvals),
        "attempts": int(state.get("attempts") or 0),
        "test_result": state.get("test_result") or {},
        "review": state.get("review") or {},
        "approvals": approvals,
        "experience_hits": state.get("experience_hits") or [],
        "evidence_gate": state.get("evidence_gate") or {},
        "evidence_cards": state.get("evidence_cards") or [],
        "evidence_trace": state.get("evidence_trace") or [],
        "evidence_mismatch": state.get("evidence_mismatch") or {},
        "model": str(configurable.get("model") or ""),
        "model_tier": str(state.get("model_tier") or ""),
        "model_used": str(state.get("model_used") or ""),
        "llm_calls": int(state.get("llm_calls") or 0),
        "estimated_tokens": int(state.get("estimated_tokens") or 0),
        "status": _status(state),
    }
    return _safe(record)


def trajectory_path(config: dict[str, Any]) -> Path:
    configured = (config.get("configurable") or {}).get("trajectory_path")
    return Path(str(configured)).expanduser() if configured else DEFAULT_TRAJECTORY_PATH


def append_trajectory(record: dict[str, Any], path: Path) -> None:
    """追加一条 JSONL；使用单次 append，避免覆盖此前的任务记录。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def aggregate_trajectories(path: Path) -> dict[str, float | int]:
    """聚合 JSONL 的基础指标；坏行跳过，方便长期积累后仍可读。"""
    records: list[dict[str, Any]] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                records.append(item)
    total = len(records)
    if not total:
        return {"tasks": 0, "success_rate": 0.0, "avg_attempts": 0.0, "avg_tool_calls": 0.0, "avg_duration_seconds": 0.0}
    return {
        "tasks": total,
        "success_rate": round(sum(r.get("status") == "succeeded" for r in records) / total, 4),
        "avg_attempts": round(sum(float(r.get("attempts") or 0) for r in records) / total, 3),
        "avg_tool_calls": round(sum(len(r.get("tool_calls") or []) for r in records) / total, 3),
        "avg_duration_seconds": round(sum(float(r.get("duration_seconds") or 0) for r in records) / total, 3),
    }
