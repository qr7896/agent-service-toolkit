"""检索动作的统一接口（doc §31）。

把"检索"从一次 Top-K，变成**一组可被策略挑选的动作**。每个动作自己声明：

  fills     补哪一维证据（target / impact / verification / episodic）
  cost      相对成本（工具调用 + token 的粗估权重）
  risk      把 Agent 带向错误上下文的风险
  can_run   在当前状态下能不能做（例如还不知道目标符号时，查调用方没有意义）
  run       真的执行，返回观察文本

动作执行本身**不含 LLM**：全是确定性工具与静态索引，所以策略挑选动作时不花模型调用。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents import code_intel
from agents.code_tools import PROJECT_ROOT
from agents.evidence import EvidenceState


@dataclass
class Observation:
    action: str
    text: str
    filled: str
    # 这次观察里"新出现"的证据点（文件 / 符号 / 测试），供指标统计用
    artifacts: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class RetrievalAction:
    name: str
    fills: str
    cost: float
    risk: float
    runner: Callable[[str, dict[str, Any], Path], str]
    requires: str = ""  # 依赖哪个已有证据（为空则不依赖）

    def can_run(self, state: EvidenceState) -> bool:
        if not self.requires:
            return True
        return getattr(state, self.requires, 0.0) > 0.0

    def run(self, query: str, plan: dict[str, Any], root: Path | None = None) -> Observation:
        base = Path(root or PROJECT_ROOT)
        text = self.runner(query, plan, base) or ""
        return Observation(
            action=self.name,
            text=text,
            filled=self.fills,
            artifacts=extract_artifacts(text),
        )


def extract_artifacts(text: str) -> dict[str, list[str]]:
    """从观察文本里抽出 文件 / 符号 / 测试——指标全靠它算。"""
    files: set[str] = set()
    symbols: set[str] = set()
    tests: set[str] = set()
    for line in str(text or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        head = stripped.split()[0]
        if ":" in head and "/" in head or head.endswith(".py"):
            files.add(head.split(":")[0].replace("\\", "/"))
        if "::" in stripped:
            tests.add(stripped.split()[0])
        parts = stripped.replace(":", " ").split()
        if len(parts) >= 3 and parts[0].endswith(".py"):
            symbols.add(parts[-1])
        elif len(parts) >= 2 and parts[0] in {"caller", "callee"}:
            symbols.add(parts[-1])
    return {
        "files": sorted(files),
        "symbols": sorted(symbols),
        "tests": sorted(tests),
    }


def _target_symbol(query: str, plan: dict[str, Any]) -> str:
    """优先用计划里点名的符号，其次退回查询里的标识符。"""
    for step in plan.get("steps") or []:
        for token in str(step.get("reason") or "").split():
            if "_" in token or token[:1].isupper():
                return token.strip("`.,:;()")
    tokens = [t for t in str(query or "").split() if "_" in t or t[:1].isupper()]
    return tokens[0].strip("`.,:;()") if tokens else str(query or "").strip()[:40]


ACTIONS: dict[str, RetrievalAction] = {
    # --- target 证据 ---
    "lexical_search": RetrievalAction(
        "lexical_search",
        "target",
        1.5,
        0.3,
        lambda q, plan, root: code_intel.symbol_search(_target_symbol(q, plan), root),
    ),
    "symbol_search": RetrievalAction(
        "symbol_search",
        "target",
        1.0,
        0.1,
        lambda q, plan, root: code_intel.symbol_search(_target_symbol(q, plan), root),
    ),
    "list_symbols_in_file": RetrievalAction(
        "list_symbols_in_file",
        "target",
        1.0,
        0.1,
        lambda q, plan, root: "\n".join(
            code_intel.symbols_in_file(str(step.get("path") or ""), root)
            for step in plan.get("steps") or []
        ),
    ),
    # --- impact 证据（需要先知道目标符号）---
    "get_callers": RetrievalAction(
        "get_callers",
        "impact",
        0.8,
        0.1,
        lambda q, plan, root: code_intel.get_callers(_target_symbol(q, plan), root),
        requires="target",
    ),
    "analyze_impact": RetrievalAction(
        "analyze_impact",
        "impact",
        1.2,
        0.2,
        lambda q, plan, root: code_intel.analyze_impact(_target_symbol(q, plan), root),
        requires="target",
    ),
    # --- verification 证据 ---
    "find_related_tests": RetrievalAction(
        "find_related_tests",
        "verification",
        0.9,
        0.1,
        lambda q, plan, root: code_intel.find_related_tests(_target_symbol(q, plan), root),
        requires="target",
    ),
    # --- episodic 证据（历史经验，作为先验而不是覆盖度）---
    "experience_retrieval": RetrievalAction(
        "experience_retrieval",
        "episodic",
        1.0,
        0.2,
        lambda q, plan, root: "",  # 由调用方注入 config 后走 coding_memory，见 recall_for_policy
    ),
}


def recall_for_policy(query: str, config: dict[str, Any]) -> Observation:
    """经验检索需要 config（经验库路径），所以单独一条入口。"""
    from agents.coding_memory import recall_experiences

    hits, mode = recall_experiences(query, config)
    text = "\n".join(f"{hit.get('trajectory_id')} :: {hit.get('task')}" for hit in hits)
    return Observation(
        action="experience_retrieval",
        text=text,
        filled="episodic",
        artifacts={"files": [], "symbols": [], "tests": []},
    )


def available_actions(state: EvidenceState, tried: set[str] | None = None) -> list[RetrievalAction]:
    blocked = tried or set()
    return [
        action for name, action in ACTIONS.items() if name not in blocked and action.can_run(state)
    ]


__all__ = [
    "ACTIONS",
    "Observation",
    "RetrievalAction",
    "available_actions",
    "extract_artifacts",
    "recall_for_policy",
]
