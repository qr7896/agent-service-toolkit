"""Coding Agent 的规划器（阶段 9 / Planning）。

目标：让 Agent **先出计划、再动手**，而且计划要进入 State 成为"控制中枢"，
而不是只打印给用户看（打印只是进度条，进 State 才能被后续节点读取、校验、执行）。

三段式实现：
  1) 侦察 recon：只用只读工具，最多 MAX_RECON_STEPS 轮，把相关情况看清；
  2) 规划 plan：把"需求 + 侦察结论"交给模型，要求输出**严格 JSON** 计划；
  3) 校验 validate：用确定性代码检查计划与真实仓库是否一致
     （action=modify 的文件必须存在、action=create 的文件必须不存在），
     不一致就写进 open_questions——这就是"LLM 提方案、确定性系统验事实"。

为什么不用 model.with_structured_output(...)：
  实测 DeepSeek 当前模型两条路都走不通——
    * method 默认（json_schema 形式的 response_format）→ 400 "This response_format type is unavailable now"
    * method="function_calling"（强制 tool_choice）→ 400 "Thinking mode does not support this tool_choice"
  所以这里改用"JSON 提示 + 容错解析 + Pydantic 校验"，并且把解析失败也当成一种
  可观察状态（写进 open_questions），而不是让整个图崩掉。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field, ValidationError

from agents.code_tools import PROJECT_ROOT, git_diff, list_files, read_file, search_code
from agents.coding_memory import format_experience_context, recall_experiences
from core import get_model, settings

MAX_RECON_STEPS = 3
MAX_FINDING_CHARS = 1500
MAX_FINDINGS_CHARS = 6000

# 规划阶段只允许只读工具：写权限不在这一环（对应 v3 §13 / §37）
PLANNER_TOOLS = [list_files, search_code, read_file, git_diff]
_TOOL_BY_NAME = {t.name: t for t in PLANNER_TOOLS}


class PlanStep(BaseModel):
    order: int = Field(description="执行顺序，从 1 开始")
    action: Literal["create", "modify"]
    path: str = Field(description="相对项目根的文件路径")
    reason: str = Field(description="为什么改这个文件")


class Plan(BaseModel):
    task: str = Field(description="一句话复述需求")
    steps: list[PlanStep] = Field(default_factory=list)
    verification: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


RECON_PROMPT = """你是 Coding Agent 的侦察员。用户会给你一个开发需求，
你的任务是先用只读工具把相关情况看清楚：

- list_files 看目录结构，search_code 定位相关代码，read_file 读关键文件，
  git_diff 看当前工作区改动；
- 你没有写权限，只能看；
- 最多几轮就要收敛，不要试图读完整仓库；
- 信息够了就直接回复"信息足够"，不要再调用工具。
"""

PLAN_PROMPT = """你是 Coding Agent 的规划器。请基于"需求 + 侦察结果"产出一份可执行的修改计划。

严格要求：
1. 只输出一个 JSON 对象，不要输出任何解释文字，不要用 Markdown 代码围栏。
2. JSON 结构固定为：
{
  "task": "一句话复述需求",
  "steps": [
    {"order": 1, "action": "create", "path": "相对项目根的路径", "reason": "为什么改这里"}
  ],
  "verification": ["怎么验证，例如 python -m pytest -q tests/schema"],
  "open_questions": ["需求里没讲清、必须先确认的问题"]
}
3. steps 按执行顺序排列；action 只能是 "create" 或 "modify"；
   action=modify 的文件必须是仓库里真实存在的，action=create 的文件应当还不存在。
4. verification 至少一条**可执行**的验证方式（测试命令或明确的检查点）。
5. 需求信息不足时（没说改哪个模块、达到什么标准、是否需要兼容旧行为等），
   把问题写进 open_questions，不要在 steps 里瞎猜。
6. 不要计划引入大型新依赖，也不要把范围扩到当前仓库之外。
7. 如果给了"历史经验"：它来自真实轨迹，accepted 表示这类做法通过了测试，
   rejected 表示这类做法失败过、应当避开。经验只是参考，**不能替代你对当前仓库的侦察**；
   经验与当前代码冲突时，以你实际读到的代码为准。
"""


def build_plan_user_message(
    requirement: str, findings: str, experience_context: str = ""
) -> str:
    """拼装规划阶段的用户消息。

    `experience_context` 为空时输出与阶段 15 之前逐字一致——没有相关经验，
    行为就不该发生任何变化。
    """
    parts = [
        f"需求：{requirement}",
        f"仓库侦察结果（可能不完整，仅供参考）：\n{findings or '（未做侦察）'}",
    ]
    if experience_context:
        parts.append(experience_context)
    return "\n\n".join(parts)


def _extract_json_object(text: str) -> str | None:
    """从可能夹杂解释文字/代码围栏的文本里，抠出第一个平衡的 JSON 对象。"""
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _parse_plan(text: str) -> Plan | None:
    """把模型输出解析成 Plan；解析不出来就返回 None（由调用方兜底）。"""
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
        plan = Plan.model_validate(data)
    except ValidationError:
        return None
    plan.steps = sorted(plan.steps, key=lambda s: s.order)
    return plan


def _validate_plan(plan: Plan) -> Plan:
    """用确定性检查把"模型说的"和"仓库真实状态"对齐。

    发现的问题不丢弃，而是追加到 open_questions —— 这样后续节点和人能看到
    "计划本身有问题"，而不是执行到一半才失败。
    """
    issues: list[str] = []
    for step in plan.steps:
        rel = Path(step.path.replace("\\", "/"))
        if rel.is_absolute() or ".." in rel.parts:
            issues.append(f"计划里的路径越权：{step.path}")
            continue
        exists = (PROJECT_ROOT / rel).exists()
        if step.action == "modify" and not exists:
            issues.append(f"计划要修改的文件不存在：{step.path}")
        elif step.action == "create" and exists:
            issues.append(f"计划要新建的文件已存在：{step.path}")
    if not plan.steps and not plan.open_questions:
        issues.append("规划器没有给出可执行的步骤，需要更明确的需求")
    if issues:
        plan.open_questions = [*plan.open_questions, *issues]
    return plan


def _last_human_text(messages: list[Any]) -> str:
    for msg in reversed(messages):
        if getattr(msg, "type", "") == "human" or msg.__class__.__name__ == "HumanMessage":
            return str(getattr(msg, "content", "") or "")
    return ""


def recon_steps(config: RunnableConfig) -> int:
    """侦察轮数上限：默认 3；需求已经把目标文件说清楚时可以调小以省调用。"""
    raw = (config.get("configurable") or {}).get("planner_recon_steps", MAX_RECON_STEPS)
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return MAX_RECON_STEPS


async def _recon(model: Any, requirement: str, steps: int = MAX_RECON_STEPS) -> str:
    """只读侦察：最多 MAX_RECON_STEPS 轮工具调用，返回拼接后的发现（有长度上限）。"""
    bound = model.bind_tools(PLANNER_TOOLS)
    messages: list[Any] = [
        SystemMessage(content=RECON_PROMPT),
        HumanMessage(content=f"开发需求：{requirement}"),
    ]
    findings: list[str] = []
    for _ in range(steps):
        ai = await bound.ainvoke(messages)
        messages.append(ai)
        calls = getattr(ai, "tool_calls", None) or []
        if not calls:
            break
        for call in calls:
            tool = _TOOL_BY_NAME.get(call.get("name", ""))
            if tool is None:
                result = f"ERROR: 侦察阶段不允许调用工具 {call.get('name')}"
            else:
                try:
                    result = str(tool.invoke(call.get("args") or {}))
                except Exception as e:  # 工具失败也不该炸掉规划
                    result = f"ERROR: {e}"
            messages.append(ToolMessage(content=result, tool_call_id=call.get("id", "")))
            findings.append(f"[{call.get('name')}({call.get('args')})]\n{result[:MAX_FINDING_CHARS]}")
    joined = "\n\n".join(findings)
    return joined[:MAX_FINDINGS_CHARS]


async def planner(state: dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
    """规划节点：侦察 → 产出结构化计划 → 确定性校验 → 写进 State 的 plan 字段。"""
    requirement = _last_human_text(state.get("messages", []))
    model = get_model(config["configurable"].get("model", settings.DEFAULT_MODEL))

    findings = await _recon(model, requirement, recon_steps(config))
    hits, retrieval = recall_experiences(requirement, config)
    plan_messages = [
        SystemMessage(content=PLAN_PROMPT),
        HumanMessage(content=build_plan_user_message(requirement, findings, format_experience_context(hits))),
    ]
    ai = await model.ainvoke(plan_messages)
    parsed = _parse_plan(str(getattr(ai, "content", "") or ""))
    if parsed is None:
        parsed = Plan(
            task=requirement or "（未提供需求）",
            steps=[],
            verification=[],
            open_questions=[
                "规划器输出无法解析为 JSON，需要重新规划或把需求说得更具体",
                f"原始输出片段：{str(getattr(ai, 'content', ''))[:200]}",
            ],
        )
    plan = _validate_plan(parsed)
    return {
        "plan": plan.model_dump(),
        "experience_hits": [{**hit, "retrieval": retrieval, "phase": "planning"} for hit in hits],
    }
