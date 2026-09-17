"""EGCP：证据门控式规划（doc 01）。

核心问题：**Coding Agent 什么时候"已经看够了代码"，什么时候该继续取证据，什么时候该停？**
本模块把这件事从"模型觉得自己懂了"变成**可计算对象**：

  EvidenceState  = {target, impact, verification, risk, queries_used}
  EvidenceCard   = 每个计划步骤掌握的结构证据（符号 / 调用方 / 相关测试）
  EvidenceGate   = 三个维度都过线才允许进入写阶段
  Evidence Debt  = 还欠哪一维证据；欠债就不许写
  Reconciliation = 改完拿真实 diff / 测试反查修改前的预测

**证据全部来自确定性代码事实**（`code_intel` 的索引），不采信模型自述；因此评估计划、
判断门控、选择下一步取证动作都不需要额外 LLM 调用——这一点很重要：如果"判断证据够不够"
本身要花一次模型调用，那这个门控就成了成本来源而不是能力。

已知边界：本地索引只看得到 Python 静态调用关系，动态分发、生成代码、跨语言引用都看不到，
所以 `impact` 可能低估。接入真正的 CodeGraph 后，替换 `code_intel` 的实现即可，本模块不动。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import re

from agents import code_intel

# 第一版阈值（doc 01 §8）：研究时应由验证集校准，而不是拍死
DEFAULT_THRESHOLDS = {"target": 0.8, "impact": 0.6, "verification": 0.6}
LAMBDA_RISK = 0.5
EPS = 0.1
MAX_EVIDENCE_ROUNDS = 2

# 证据动作空间（doc 01 §6）。local_action 是本地实现能真正执行的动作；None 表示当前不可用。
ACTION_SPACE: dict[str, dict[str, Any]] = {
    "symbol_search": {"fills": "target", "cost": 1.0, "risk": 0.1},
    "get_ai_context": {"fills": "target", "cost": 1.5, "risk": 0.15},
    "get_callers": {"fills": "impact", "cost": 1.0, "risk": 0.1},
    "get_callees": {"fills": "impact", "cost": 1.0, "risk": 0.1},
    "analyze_impact": {"fills": "impact", "cost": 1.5, "risk": 0.2},
    "find_related_tests": {"fills": "verification", "cost": 1.0, "risk": 0.1},
    "search_code": {"fills": "target", "cost": 1.5, "risk": 0.3},
    "read_file": {"fills": "target", "cost": 2.0, "risk": 0.2},
    "git_diff": {"fills": "impact", "cost": 1.0, "risk": 0.1},
    "run_tests": {"fills": "verification", "cost": 3.0, "risk": 0.2},
    "ask_clarification": {"fills": "abstain", "cost": 0.2, "risk": 0.0},
}


@dataclass
class EvidenceState:
    target: float = 0.0
    impact: float = 0.0
    verification: float = 0.0
    risk: float = 0.0
    queries_used: int = 0
    tokens_spent: int = 0


@dataclass
class EvidenceCard:
    order: int
    path: str
    target_symbols: list[str] = field(default_factory=list)
    callers: list[str] = field(default_factory=list)
    related_tests: list[str] = field(default_factory=list)
    impact_level: str = "none"
    impact_analysis: str = ""


@dataclass
class GateDecision:
    passed: bool
    debt: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    state: EvidenceState = field(default_factory=EvidenceState)
    rounds_used: int = 0
    actions_taken: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class EvidenceMismatch:
    predicted_paths: list[str] = field(default_factory=list)
    actual_paths: list[str] = field(default_factory=list)
    unexpected: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    test_passed: bool = False

    @property
    def detected(self) -> bool:
        return bool(self.unexpected or self.missing)


def _identifier_tokens(text: str) -> list[str]:
    """从自然语言里挑出可能是标识符的词（下划线或驼峰）。"""
    tokens: list[str] = []
    for raw in str(text or "").replace("`", " ").replace("(", " ").replace(")", " ").split():
        token = raw.strip(".,:;、，。：\"'[]{}")
        if "_" in token or any(ch.isupper() for ch in token[1:]):
            if token.isascii() and len(token) > 2:
                tokens.append(token)
    return tokens


def evaluate_step(step: dict[str, Any], task: str = "", root: Path | None = None) -> EvidenceCard:
    """给一个计划步骤生成证据卡：只写"我查到了什么"，不写"我觉得"。"""
    index = code_intel.build_index(root)
    path = str(step.get("path") or "")
    text = f"{step.get('reason') or ''} {task}"
    symbols_in_file = {
        symbol.name: symbol
        for symbols in index.symbols.values()
        for symbol in symbols
        if symbol.path == path
    }
    # 用"已知符号名 + 词边界"匹配，而不是猜标识符形状：
    # 只认 snake_case / 驼峰会让 add 这类普通小写函数名被漏掉（踩过）。
    named = [
        name for name in sorted(symbols_in_file)
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", text)
    ]
    chosen = named or (sorted(symbols_in_file)[:1] if len(symbols_in_file) == 1 else [])

    callers: list[str] = []
    related_tests: list[str] = []
    impact_level = "none"
    analysis = ""
    for name in chosen[:3]:
        callers += sorted(index.callers.get(name, set()))
        tests = set(index.tests.get(name, set()))
        for caller in index.callers.get(name, set()):
            tests |= index.tests.get(caller, set())
        related_tests += sorted(tests)
        report = code_intel.analyze_impact(name, root)
        impact_level = _max_level(impact_level, _level_of(report))
        analysis = report if not analysis else f"{analysis}\n{report}"

    return EvidenceCard(
        order=int(step.get("order") or 0),
        path=path,
        target_symbols=chosen,
        callers=sorted(set(callers)),
        related_tests=sorted(set(related_tests)),
        impact_level=impact_level,
        impact_analysis=analysis,
    )


def _level_of(report: str) -> str:
    for line in report.splitlines():
        if line.startswith("impact_level:"):
            return line.split(":", 1)[1].strip()
    return "none"


def _max_level(*levels: str) -> str:
    order = {"none": 0, "low": 1, "medium": 2, "high": 3}
    return max(levels, key=lambda level: order.get(level, 0))


def state_from_cards(cards: list[EvidenceCard], plan: dict[str, Any], root: Path | None = None) -> EvidenceState:
    """把证据卡折算成 0~1 的三维覆盖度。规则固定、可解释、可复现。"""
    if not cards:
        return EvidenceState()
    target_scores: list[float] = []
    impact_scores: list[float] = []
    verification_scores: list[float] = []
    verification_plan = [str(v) for v in (plan.get("verification") or [])]
    for card in cards:
        exists = (Path(root or code_intel.PROJECT_ROOT) / card.path).exists() if card.path else False
        if not exists:
            target_scores.append(0.0)
        elif card.target_symbols:
            target_scores.append(1.0)
        else:
            target_scores.append(0.4)  # 知道文件但不知道具体符号

        impact_scores.append({"none": 0.0, "low": 0.4, "medium": 0.8, "high": 1.0}[card.impact_level])

        if card.related_tests:
            verification_scores.append(1.0)
        elif any(str(item).split()[0].endswith(".py") for item in verification_plan):
            verification_scores.append(0.6)  # 计划里写了测试文件，但没确认它覆盖目标
        else:
            verification_scores.append(0.0)

    def _mean(values: list[float]) -> float:
        return round(sum(values) / len(values), 3) if values else 0.0

    return EvidenceState(
        target=_mean(target_scores),
        impact=_mean(impact_scores),
        verification=_mean(verification_scores),
    )


def detect_gaps(state: EvidenceState, thresholds: dict[str, float] | None = None) -> list[str]:
    limits = thresholds or DEFAULT_THRESHOLDS
    return [dim for dim, limit in limits.items() if getattr(state, dim) < limit]


def score_action(action: str, gaps: list[str]) -> float:
    """Utility = 预期证据增益 / (成本 + λ×风险)。增益按"缺口在列表里的位置"递减。"""
    spec = ACTION_SPACE.get(action)
    if not spec:
        return 0.0
    dimension = spec["fills"]
    if dimension == "abstain" or dimension not in gaps:
        return 0.0
    rank = gaps.index(dimension)
    gain = 1.0 if rank == 0 else 0.6 / rank
    return round(gain / (spec["cost"] + LAMBDA_RISK * spec["risk"] + EPS), 4)


def pick_action(gaps: list[str]) -> str:
    """选当前最高效的取证动作；没有任何动作能补缺口时退回"问人"。"""
    scored = [(score_action(action, gaps), action) for action in ACTION_SPACE]
    scored = [item for item in scored if item[0] > 0]
    if not scored:
        return "ask_clarification"
    return max(scored)[1]


def execute_action(action: str, plan: dict[str, Any], root: Path | None = None) -> str:
    """执行只读取证动作，返回给规划器看的证据文本。写操作不在动作空间里。"""
    cards = [evaluate_step(step, plan.get("task") or "", root) for step in plan.get("steps") or []]
    symbols = [name for card in cards for name in card.target_symbols]
    query = symbols[0] if symbols else _fallback_symbol_query(plan)
    if action in {"symbol_search", "search_code"}:
        return code_intel.symbol_search(query, root)
    if action == "get_callers":
        return code_intel.get_callers(query, root)
    if action == "get_callees":
        return code_intel.get_callees(query, root)
    if action == "analyze_impact":
        return code_intel.analyze_impact(query, root)
    if action == "find_related_tests":
        return code_intel.find_related_tests(query, root)
    if action == "get_ai_context":
        path = (plan.get("steps") or [{}])[0].get("path") or ""
        return code_intel.symbol_search(Path(path).stem if path else query, root)
    return f"（{action} 需要模型参与，本阶段只自动执行确定性动作）"


def _fallback_symbol_query(plan: dict[str, Any]) -> str:
    tokens = _identifier_tokens(plan.get("task") or "")
    return tokens[0] if tokens else (plan.get("task") or "").strip()[:30]


def audit_plan(
    plan: dict[str, Any],
    root: Path | None = None,
    thresholds: dict[str, float] | None = None,
    max_rounds: int = MAX_EVIDENCE_ROUNDS,
) -> tuple[GateDecision, list[EvidenceCard], list[dict[str, Any]]]:
    """Evidence Gate 主流程：评估 → 缺口 → 主动取证 → 复评 → 通过或弃权。

    返回 (门控结论, 证据卡, 取证轨迹)。取证轨迹会写进 trajectory，用于事后归因。
    """
    cards = [evaluate_step(step, plan.get("task") or "", root) for step in plan.get("steps") or []]
    state = state_from_cards(cards, plan, root)
    limits = thresholds or DEFAULT_THRESHOLDS
    trace: list[dict[str, Any]] = []
    rounds = 0

    while rounds < max_rounds:
        gaps = detect_gaps(state, limits)
        if not gaps:
            break
        action = pick_action(gaps)
        if action == "ask_clarification":
            break
        observation = execute_action(action, plan, root)
        rounds += 1
        state.queries_used += 1
        trace.append(
            {"round": rounds, "action": action, "filled": gaps[0], "observation": observation[:800]}
        )
        cards = [evaluate_step(step, plan.get("task") or "", root) for step in plan.get("steps") or []]
        new_state = state_from_cards(cards, plan, root)
        # 只保留本轮真正提升的维度，避免"原地打转"被当成进展
        for dim in ("target", "impact", "verification"):
            setattr(new_state, dim, max(getattr(state, dim), getattr(new_state, dim)))
        new_state.queries_used = state.queries_used
        new_state.tokens_spent = state.tokens_spent
        state = new_state

    debt = detect_gaps(state, limits)
    decision = GateDecision(
        passed=not debt,
        debt=debt,
        rejected=[],
        state=state,
        rounds_used=rounds,
        actions_taken=[item["action"] for item in trace],
        reason="证据充分" if not debt else f"证据不足：{', '.join(debt)}",
    )
    return decision, cards, trace


def reconcile(
    plan: dict[str, Any],
    actual_paths: list[str],
    test_passed: bool,
) -> EvidenceMismatch:
    """修改后对账：预测要改的文件 vs 真实改动的文件（doc 01 §11）。"""
    predicted = [str(step.get("path")) for step in plan.get("steps") or [] if step.get("path")]
    predicted_set, actual_set = set(predicted), set(actual_paths)
    return EvidenceMismatch(
        predicted_paths=sorted(predicted_set),
        actual_paths=sorted(actual_set),
        unexpected=sorted(actual_set - predicted_set),
        missing=sorted(predicted_set - actual_set),
        test_passed=test_passed,
    )


def decision_to_dict(decision: GateDecision) -> dict[str, Any]:
    data = asdict(decision)
    data["thresholds"] = DEFAULT_THRESHOLDS
    return data


__all__ = [
    "ACTION_SPACE",
    "DEFAULT_THRESHOLDS",
    "EvidenceCard",
    "EvidenceMismatch",
    "EvidenceState",
    "GateDecision",
    "audit_plan",
    "decision_to_dict",
    "detect_gaps",
    "evaluate_step",
    "execute_action",
    "pick_action",
    "reconcile",
    "score_action",
    "state_from_cards",
]
