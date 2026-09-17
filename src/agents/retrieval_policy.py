"""检索策略：确定性规则版（doc §32 的 V0）。

**不让 LLM 决定下一步搜什么**——那样既花调用又难解释。这里就是一条算式：

    utility(a) = 预期证据增益 / (成本 + λ×风险)

候选只包含"当前状态允许 + 还没试过"的动作；没有候选就是 abstain。
等有了足够 trajectory，再考虑学习型策略（V3），现在不做。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents.evidence import (
    DEFAULT_THRESHOLDS,
    EvidenceState,
    LAMBDA_RISK,
    detect_gaps,
)
from agents.retrieval_actions import ACTIONS, Observation, RetrievalAction, available_actions


@dataclass
class Plan:
    """一次策略决策的结果，可直接写进 trajectory。"""

    action: str = ""
    utility: float = 0.0
    gaps: list[str] = field(default_factory=list)
    considered: list[tuple[str, float]] = field(default_factory=list)
    reason: str = ""

    @property
    def abstained(self) -> bool:
        return not self.action


def utility(action: RetrievalAction, state: EvidenceState, thresholds: dict[str, float] | None = None) -> float:
    """预期增益按"缺口在列表里的位置"递减——先补最缺的那一维。"""
    gaps = detect_gaps(state, thresholds or DEFAULT_THRESHOLDS)
    if action.fills not in gaps:
        return 0.0
    rank = gaps.index(action.fills)
    gain = 1.0 if rank == 0 else 0.6 / rank
    return round(gain / (action.cost + LAMBDA_RISK * action.risk + 0.1), 4)


def choose(
    state: EvidenceState,
    tried: set[str] | None = None,
    thresholds: dict[str, float] | None = None,
) -> Plan:
    """选下一个检索动作；选不出来就是 abstain（不猜）。"""
    gaps = detect_gaps(state, thresholds or DEFAULT_THRESHOLDS)
    if not gaps:
        return Plan(gaps=gaps, reason="证据已充分，停止检索")
    candidates = available_actions(state, tried)
    scored = sorted(
        ((action, utility(action, state, thresholds)) for action in candidates),
        key=lambda pair: pair[1],
        reverse=True,
    )
    scored = [(action, value) for action, value in scored if value > 0]
    if not scored:
        return Plan(
            gaps=gaps,
            reason=f"没有可用动作能补 {gaps}：证据取不到，应交给人确认",
            considered=[(action.name, 0.0) for action in candidates],
        )
    best, value = scored[0]
    return Plan(
        action=best.name,
        utility=value,
        gaps=gaps,
        considered=[(action.name, score) for action, score in scored],
        reason=f"补 {best.fills}：utility={value}",
    )


def execute(action_name: str, query: str, plan: dict[str, Any], root: Path | None = None) -> Observation:
    """执行选中的动作。找不到动作名就返回空观察，由调用方决定怎么记。"""
    action = ACTIONS.get(action_name)
    if action is None:
        return Observation(action=action_name, text="", filled="")
    return action.run(query, plan, root)


__all__ = ["Plan", "choose", "execute", "utility"]
