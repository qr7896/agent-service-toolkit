"""最基本的成本控制 + 模型路由（v5 §40 / 阶段 21）。

本阶段的成本控制**只做最基本的**，不追求花哨的分层策略：

  1. **账面可见**：每次 LLM 调用都累加 `llm_calls` 与 `estimated_tokens` 并写进轨迹，
     让"这个任务花了多少"有据可查，而不是凭感觉；
  2. **能用免费的就用免费的**：只有真正配置了本地模型（如 Ollama）时才把它放进阶梯，
     简单任务优先走本地；没配置就直接用默认档，不假装有一台不存在的本地模型；
  3. **预算超了就冻结升级**：`budget_tokens` 用尽后不再往上换更贵的模型，
     重试次数仍由 `MAX_RETRIES` 决定——成本控制不越权去改任务终止条件。

**最高档就是 `deepseek-v4-flash`**：本项目不引入更贵的模型档位，所以阶梯只有
`local（若配置）→ cheap(flash)`。换句话说，这里的"路由"主要不是换更强模型，
而是"该省则省、该记则记"，以及在没有更贵模型可买的前提下把花费看清楚。

一条硬约束：`model_routing` 不在 config 里时，`route_model()` 原样返回今天用的
`model`，行为逐字不变——不启用就等于不存在。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from core import settings

Tier = Literal["local", "cheap", "strong"]
TIER_ORDER: tuple[Tier, ...] = ("local", "cheap")

DEFAULT_CHEAP_MODEL = "deepseek-v4-flash"

# 粗略的 token 估算：英文约 4 字符 1 token，中文更密，这里取偏保守的 3。
CHARS_PER_TOKEN = 3
MESSAGE_OVERHEAD_TOKENS = 40


@dataclass
class RoutingDecision:
    model: str
    tier: Tier
    routing_enabled: bool
    escalated: bool = False
    budget_exhausted: bool = False
    reasons: list[str] = field(default_factory=list)


def _conf(config: Any) -> dict[str, Any]:
    return (config or {}).get("configurable") or {}


def routing_enabled(config: Any) -> bool:
    return bool(_conf(config).get("model_routing", False))


def tier_model(tier: Tier, config: Any) -> str:
    conf = _conf(config)
    if tier == "local":
        return str(conf.get("local_model") or settings.OLLAMA_MODEL or "")
    return str(conf.get("cheap_model") or DEFAULT_CHEAP_MODEL)


def ladder(config: Any, upto: int = 1) -> list[Tier]:
    """可用阶梯。没配本地模型时本地档直接不出现，而不是让它在运行时失败。"""
    tiers: list[Tier] = list(TIER_ORDER[: upto + 1])
    if not tier_model("local", config):
        tiers = [t for t in tiers if t != "local"]
    return tiers


def estimate_tokens(*texts: Any) -> int:
    """确定性估算（不调用 tokenizer）：够用来比较同一条链路里的相对消耗。"""
    total = 0
    for text in texts:
        if text is None:
            continue
        total += len(str(text)) // CHARS_PER_TOKEN + MESSAGE_OVERHEAD_TOKENS
    return total


def task_complexity(state: Any) -> int:
    """0=简单 1=中等 2=复杂。用可解释的确定性信号，不靠模型自我评估。"""
    plan = state.get("plan") or {}
    steps = plan.get("steps") or []
    questions = plan.get("open_questions") or []
    score = 0
    if len(steps) > 1:
        score += 1
    if len(steps) > 3:
        score += 1
    if questions:
        score += 1
    return min(2, score)


def base_tier(state: Any, config: Any, role: str) -> Tier:
    """起点：能用免费档就用免费档；复杂任务直接上默认档，别在关键处省错地方。"""
    available = ladder(config)
    if available[0] == "local" and task_complexity(state) >= 2:
        return available[-1]
    return available[0]


def route_model(
    state: Any,
    config: Any,
    role: str,
) -> RoutingDecision:
    """给某个节点选模型。未启用路由时原样返回配置里的 `model`。"""
    conf = _conf(config)
    if not routing_enabled(config):
        model = str(conf.get("model") or settings.DEFAULT_MODEL)
        return RoutingDecision(model=model, tier="cheap", routing_enabled=False)

    available = ladder(config)
    start = base_tier(state, config, role)
    start_index = available.index(start)

    # 失败升级：已经失败的次数直接换算成上探档位（仅对会失败的执行类节点生效）
    attempts = int(state.get("attempts") or 0)
    escalate = role in {"coder", "planner"} and attempts > 0
    target_index = min(start_index + (attempts if escalate else 0), len(available) - 1)

    reasons = [f"role={role}", f"complexity={task_complexity(state)}", f"attempts={attempts}"]
    budget = conf.get("budget_tokens")
    spent = int(state.get("estimated_tokens") or 0)
    budget_exhausted = bool(budget) and spent >= int(budget)
    if budget_exhausted and target_index > start_index:
        # 超预算就不再升级：冻结在起始档，而不是直接判任务失败
        target_index = start_index
        reasons.append(f"budget_exhausted(spent={spent},budget={budget})")

    tier = available[target_index]
    reasons.append(f"tier_index={target_index}/{len(available) - 1}")
    return RoutingDecision(
        model=tier_model(tier, config) or str(conf.get("model") or settings.DEFAULT_MODEL),
        tier=tier,
        routing_enabled=True,
        escalated=target_index > start_index,
        budget_exhausted=budget_exhausted,
        reasons=reasons,
    )


__all__ = [
    "CHARS_PER_TOKEN",
    "DEFAULT_CHEAP_MODEL",
    "RoutingDecision",
    "TIER_ORDER",
    "base_tier",
    "estimate_tokens",
    "ladder",
    "route_model",
    "routing_enabled",
    "task_complexity",
    "tier_model",
]
