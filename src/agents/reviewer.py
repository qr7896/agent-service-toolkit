"""Coding Agent 的评审员（阶段 12 / Reviewer）。

职责边界（这也是本阶段的过关题）：
  - Coder 负责**改代码**；Reviewer 负责**判断这次改动是否站得住**。
  - Reviewer 没有写权限，也不应该改代码：一旦它既能评审又能修改，
    "独立审查"就不存在了——它会倾向于替自己的改动辩护，而不是挑错。

输入：原始需求 + 执行计划 + 测试结果 + 工作区 diff
输出：结构化裁决 `{"approved": bool, "score": float, "issues": [...], "summary": str}`，
      写进 State 的 `review` 字段，并由节点追加一条人类可读的结论消息。

解析策略与 planner 一致（DeepSeek 不支持 json_schema / 强制 tool_choice）：
JSON 提示 + 括号配平提取 + Pydantic 校验；解析失败时按**未通过**处理，
绝不默认 approved=True。
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field, ValidationError

from agents.code_tools import git_diff, list_files, read_file, search_code
from agents.coding_planner import _extract_json_object
from agents.model_router import estimate_tokens, route_model
from agents.test_tools import run_tests
from core import get_model

# 评审阶段只读：结构上就不给写工具（验收脚本会断言这一点）
REVIEWER_TOOLS = [git_diff, read_file, search_code, list_files, run_tests]

MAX_DIFF_CHARS = 4000
MAX_OUTPUT_CHARS = 2000


class Review(BaseModel):
    approved: bool
    score: float = 0.0
    issues: list[str] = Field(default_factory=list)
    summary: str = ""


REVIEW_PROMPT = """你是 Coding Agent 的评审员（Reviewer）。你没有写权限，也不应该改代码——
你的唯一职责是对"这一次改动"做独立裁决。

你会看到四样东西：原始需求、执行计划、测试结果、工作区 diff。
必须逐条检查：
1) diff 是否真的覆盖了计划里要改的文件？有没有改动无关文件？
2) 改动是否直接服务于需求？有没有顺手重构、改风格、动无关代码？
3) 测试结果是否可信？只有 status=passed 才算通过；
   no_tests / error / timeout 都不算通过。
4) 有没有明显风险？例如删代码、改配置、硬编码、绕过测试、吞掉异常。
5) 有没有遗漏？需求里明确提到的东西是否都实现了？

输出要求：
- 只输出一个 JSON 对象，不要任何解释文字，不要 Markdown 代码围栏；
- 结构固定为：
{
  "approved": true,
  "score": 0.0,
  "issues": ["具体问题，必须引用 文件名:行号 或 diff 中的具体行"],
  "summary": "一句话结论"
}

判定标准：
- 只有"改动与需求一致 + 测试真的 passed + 没有明显风险"才允许 approved=true；
- diff 为空、测试不是 passed、或改动与需求无关时，必须 approved=false，并在 issues 里写清依据；
- issues 里不许写没有依据的猜测；没有问题就给空数组；
- 不要因为文件是**新增/未跟踪**就否决——评审判断的是"改动是否与需求一致、
  测试是否真的通过、有没有无关改动"，而不是文件的 git 跟踪状态。
"""


def _parse_review(text: str) -> Review | None:
    """把模型输出解析成 Review；解析不出来返回 None（由调用方按未通过处理）。"""
    raw = _extract_json_object(text or "")
    if not raw:
        return None
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    try:
        review = Review.model_validate(data)
    except ValidationError:
        return None
    review.score = max(0.0, min(1.0, float(review.score)))
    return review


def _fallback_review(reason: str, raw: str = "") -> Review:
    """兜底裁决：解析失败时按"未通过"处理，绝不默认批准。"""
    issues = [reason]
    if raw:
        issues.append(f"原始输出片段：{raw[:200]}")
    return Review(
        approved=False, score=0.0, issues=issues, summary="评审器输出不可用，按未通过处理"
    )


def format_verdict(review: Review) -> str:
    """把裁决渲染成人类可读的一段话（作为最终消息返回给调用方）。"""
    tag = "[APPROVED]" if review.approved else "[CHANGES REQUESTED]"
    lines = [
        f"{tag} 评审结论：{'通过' if review.approved else '未通过'}（score={review.score:.2f}）"
    ]
    if review.summary:
        lines.append(f"摘要：{review.summary}")
    if review.issues:
        lines.append("发现的问题：")
        lines.extend(f"- {issue}" for issue in review.issues)
    return "\n".join(lines)


def _first_human_text(messages: list[Any]) -> str:
    for msg in messages:
        if msg.__class__.__name__ == "HumanMessage":
            return str(getattr(msg, "content", "") or "")
    return ""


def _review_scope(state: dict[str, Any], config: RunnableConfig) -> str:
    """确定评审范围（diff 要限定在哪些路径上）。

    优先级：config.review_path > 计划里唯一的目标文件 > 整个仓库。

    为什么要限定范围：真实仓库里工作区可能同时存在**别人的、无关的**未提交改动，
    全仓库 diff 会把它们一起算进来，导致 reviewer 误判"改动与需求无关"。
    """
    configured = str((config.get("configurable") or {}).get("review_path") or "").strip()
    if configured:
        return configured
    steps = (state.get("plan") or {}).get("steps") or []
    paths = [str(s.get("path") or "").strip() for s in steps if s.get("path")]
    if len(paths) == 1:
        return paths[0]
    return ""


async def reviewer(state: Any, config: RunnableConfig) -> dict[str, Any]:
    """评审节点：读需求 / 计划 / 测试结果 / diff → 产出结构化裁决。"""
    decision = route_model(state, config, "reviewer")
    model = get_model(decision.model)

    requirement = _first_human_text(state.get("messages", []))
    plan = state.get("plan") or {}
    test_result = state.get("test_result") or {}
    scope = _review_scope(state, config)
    diff = str(git_diff.invoke({"path": scope} if scope else {}))

    context = (
        f"原始需求：{requirement}\n\n"
        f"执行计划：\n{json.dumps(plan, ensure_ascii=False, indent=2)}\n\n"
        f"测试结果：\n"
        f"  status: {test_result.get('status')}\n"
        f"  exit_code: {test_result.get('exit_code')}\n"
        f"  summary: {test_result.get('summary')}\n"
        f"  output（截断）：\n{(test_result.get('output') or '')[:MAX_OUTPUT_CHARS]}\n\n"
        f"评审范围：{scope or '整个仓库'}\n\n"
        f"工作区 diff（截断）：\n{diff[:MAX_DIFF_CHARS]}"
    )

    ai = await model.ainvoke([SystemMessage(content=REVIEW_PROMPT), HumanMessage(content=context)])
    raw = str(getattr(ai, "content", "") or "")
    review = _parse_review(raw) or _fallback_review("评审器输出无法解析为 JSON", raw)

    return {
        "review": review.model_dump(),
        "messages": [AIMessage(content=format_verdict(review))],
        "llm_calls": int(state.get("llm_calls") or 0) + 1,
        "estimated_tokens": int(state.get("estimated_tokens") or 0) + estimate_tokens(context, raw),
        "model_tier": decision.tier,
        "model_used": decision.model,
    }
