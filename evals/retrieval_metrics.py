"""检索质量指标（doc §20/§21）：把"检索质量"从"最终成功率"里拆出来。

为什么必须有：RAG 可能找错代码、LLM 自己猜对了、pytest 通过 —— 此时 Task Success=1
但 Retrieval Quality 很差。只看成功率会把这两种情况混在一起。

指标来源：任务的 **Gold Evidence**（gold_files / gold_symbols / gold_tests）+ 轨迹里记录的
检索观察（`retrieval_trace[*].artifacts`）。全部离线计算，不调模型。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _recall(gold: list[str], found: list[str]) -> float | None:
    if not gold:
        return None
    hits = sum(1 for item in gold if item in set(found))
    return round(hits / len(gold), 4)


def _precision(gold: list[str], found: list[str]) -> float | None:
    if not found:
        return None
    hits = sum(1 for item in found if item in set(gold))
    return round(hits / len(found), 4)


def task_metrics(record: dict[str, Any], gold: dict[str, Any]) -> dict[str, Any]:
    """单个任务的检索指标。`record` 是轨迹里的一条检索记录。"""
    trace = record.get("retrieval_trace") or []
    found_files = sorted(
        {item for step in trace for item in (step.get("artifacts") or {}).get("files", [])}
    )
    found_symbols = sorted(
        {item for step in trace for item in (step.get("artifacts") or {}).get("symbols", [])}
    )
    found_tests = sorted(
        {item for step in trace for item in (step.get("artifacts") or {}).get("tests", [])}
    )
    found_callers = sorted(
        {item for step in trace for item in (step.get("artifacts") or {}).get("callers", [])}
    )

    file_recall = _recall(list(gold.get("gold_files") or []), found_files)
    symbol_recall = _recall(list(gold.get("gold_symbols") or []), found_symbols)
    test_recall = _recall(list(gold.get("gold_tests") or []), found_tests)
    caller_recall = _recall(list(gold.get("gold_callers") or []), found_callers)
    tokens = int(record.get("estimated_tokens") or 0)
    rounds = len(trace)
    # Evidence Efficiency：recall 越高、token 越少越好。用文件/符号 recall 的均值做分子。
    recalls = [r for r in (file_recall, symbol_recall, caller_recall, test_recall) if r is not None]
    mean_recall = round(sum(recalls) / len(recalls), 4) if recalls else None
    return {
        "instance_id": record.get("instance_id") or record.get("task") or "",
        "gold_file_recall": file_recall,
        "gold_symbol_recall": symbol_recall,
        "gold_test_recall": test_recall,
        "gold_caller_recall": caller_recall,
        "context_precision": _precision(
            [*(gold.get("gold_files") or []), *(gold.get("gold_symbols") or [])],
            [*found_files, *found_symbols],
        ),
        "context_recall": mean_recall,
        "context_tokens": tokens,
        "retrieval_rounds": rounds,
        "abstained": bool(record.get("retrieval_abstained")),
        "evidence_efficiency": round(mean_recall / tokens * 1000, 4)
        if (mean_recall is not None and tokens)
        else None,
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """把逐任务指标汇总成一组均值。空值（没有 gold 或没有记录）不计入均值。"""

    def mean(key: str) -> float | None:
        values = [row[key] for row in rows if row.get(key) is not None]
        return round(sum(values) / len(values), 4) if values else None

    abstained = [row for row in rows if row.get("abstained")]
    return {
        "tasks": len(rows),
        "gold_file_recall": mean("gold_file_recall"),
        "gold_symbol_recall": mean("gold_symbol_recall"),
        "gold_test_recall": mean("gold_test_recall"),
        "gold_caller_recall": mean("gold_caller_recall"),
        "context_precision": mean("context_precision"),
        "context_recall": mean("context_recall"),
        "context_tokens": mean("context_tokens"),
        "retrieval_rounds": mean("retrieval_rounds"),
        "evidence_efficiency": mean("evidence_efficiency"),
        "abstention_rate": round(len(abstained) / len(rows), 4) if rows else None,
    }


def load_gold(path: Path) -> dict[str, dict[str, Any]]:
    """读 gold evidence JSONL：一行一个任务，键是 instance_id。"""
    import json

    gold: dict[str, dict[str, Any]] = {}
    if not Path(path).exists():
        return gold
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            gold[str(item.get("instance_id"))] = item
    return gold


__all__ = ["aggregate", "load_gold", "task_metrics"]
