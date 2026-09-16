"""Coding Agent：能看代码、按计划行事，并在放开写权限后自我修复的 Agent。

图结构（阶段 11 之后）：

    START → planner → coder → (有 tool_calls ? tools → coder : tester/END)
                        ↑                                  │
                        │                          PASS → END
                        │                          FAIL → debugger → coder
                        └───────────────           （attempts ≥ MAX_RETRIES → giveup → END）

三个关键设计：
  1) planner 产出结构化计划并写进 `State.plan`——计划要进 State 才能被后续节点
     读取、校验、执行；只打印给用户就只是个进度条。
  2) 工具执行节点 `tools` 是**自己实现的 dispatcher**（不是 ToolNode），因为工具白名单
     必须按运行模式动态决定：`allow_write=False`（默认）时写工具既不会被绑给模型，
     也会被 dispatcher 拒绝执行——两道闸门。
  3) `tester` 把 pytest 的结构化结果写进 `State.test_result`，`check_test` 依据它
     决定"结束 / 重试（debugger → coder）/ 放弃（giveup，明确报告失败）"。
     放弃时必须说清"没完成"，不许假装成功。
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.types import interrupt

from agents.code_tools import (
    PROJECT_ROOT,
    edit_file,
    git_diff,
    list_files,
    read_file,
    search_code,
    write_file,
)
from agents.coding_planner import planner
from agents.reviewer import reviewer
from agents.test_tools import run_tests
from agents.trajectory import append_trajectory, build_trajectory, trajectory_path, utc_now
from core import get_model, settings

MAX_RETRIES = 3

# 只读工具：任何时候都允许
READ_TOOLS = [search_code, read_file, list_files, git_diff, run_tests]
# 写工具：只有 allow_write=True 时才交给模型
WRITE_TOOLS = [write_file, edit_file]
ALL_TOOLS = [*READ_TOOLS, *WRITE_TOOLS]
_TOOL_BY_NAME = {t.name: t for t in ALL_TOOLS}
# 会被人工审批拦下的工具（high risk）
WRITE_TOOL_NAMES = {t.name for t in WRITE_TOOLS}

# 判定"批准"的词表：只有明确表示同意才算批准，其他一律按拒绝处理（保守默认）
APPROVE_WORDS = {
    "y", "yes", "true", "1", "ok", "approve", "approved", "confirm", "go",
    "批准", "同意", "是", "允许", "继续", "确认",
}

# 对外暴露的默认工具集（只读），供文档与验收脚本引用
TOOLS = READ_TOOLS

SYSTEM_PROMPT = """你是一个代码助手，工作在一个 Python 项目仓库里。

工作规则：
1. 先定位、再精读：用 search_code 按关键词 / 函数名 / 类名搜索，拿到 `路径:行号`，
   再用 read_file 读那几行的上下文。只有在完全不知道该搜什么时，才先用 list_files
   看看仓库结构。不要凭记忆或猜测回答。
2. 你的每个结论都必须来自你真正读到的文件内容。
3. 回答时必须给出证据：文件路径 + 行号，例如 src/run_service.py:36。
4. search_code 返回 no matches 时，换关键词、换大小写策略或放宽 path_glob 再试一次。
5. 涉及"改了什么 / 有哪些改动"的问题时，用 git_diff 读真实差异，不要凭猜测回答。
6. 涉及"能不能跑通 / 测试是否通过"的问题时，用 run_tests 真实执行 pytest，
   并按返回的 status / summary 回答；不要用"应该没问题"这类没有依据的说法。
7. 需要改代码时：先用 edit_file 做**最小修复**（不要重写整个文件），改完用 git_diff
   确认改动，再跑测试。改动必须与当前任务直接相关。
8. 只讨论这个仓库里的内容。如果文件不存在或没有权限，如实说明，不要编造。
"""


class CodingState(MessagesState):
    """在 MessagesState 基础上增加计划、测试结果与重试计数。

    - plan：规划器产出（控制中枢）
    - test_result：tester 写入的结构化测试结果
    - attempts：已经跑过几轮测试（用于重试上限）
    - allow_write：本次运行是否放开写权限（planner 节点写入）
    """

    plan: dict[str, Any]
    test_result: dict[str, Any]
    review: dict[str, Any]
    approvals: list[dict[str, Any]]
    trajectory: dict[str, Any]
    trajectory_started_at: str
    attempts: int
    allow_write: bool


def _configurable(config: RunnableConfig) -> dict[str, Any]:
    return config.get("configurable") or {}


def _allow_write(config: RunnableConfig) -> bool:
    return bool(_configurable(config).get("allow_write", False))


def _allowed_tools(config: RunnableConfig) -> list[Any]:
    return READ_TOOLS + (WRITE_TOOLS if _allow_write(config) else [])


def _require_approval(config: RunnableConfig) -> bool:
    """高风险写操作是否需要人工批准（默认需要）。"""
    return bool(_configurable(config).get("require_approval", True))


def _is_approved(value: Any) -> bool:
    """把 resume 值解释成"批准 / 拒绝"。

    - 报务端传进来的是用户输入的字符串（见 service.py 的 `Command(resume=user_input.message)`）；
    - 直接调用图时也可能传 bool 或 dict；
    - **无法识别一律按拒绝处理**——这是安全默认：宁可多问一次，也不能误执行写操作。
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, dict):
        if "approved" in value:
            return _is_approved(value["approved"])
        return False
    if isinstance(value, str):
        return value.strip().lower() in APPROVE_WORDS
    return False


def _plan_reason(state: CodingState, path: str) -> str:
    """从计划里找出这个文件对应的修改理由（审批信息里需要"为什么"）。"""
    for step in (state.get("plan") or {}).get("steps") or []:
        if str(step.get("path") or "") == path:
            return str(step.get("reason") or "")
    return ""


def _describe_action(state: CodingState, call: dict[str, Any]) -> dict[str, Any]:
    """把一次写操作整理成"人能据此决策"的信息：改哪个文件、改成什么、为什么。"""
    args = call.get("args") or {}
    name = call.get("name", "")
    path = str(args.get("path") or "")
    action: dict[str, Any] = {"tool": name, "path": path, "reason": _plan_reason(state, path)}
    if name == "write_file":
        action["change"] = f"写入/覆盖文件（内容前 200 字）：{str(args.get('content') or '')[:200]}"
        action["overwrite"] = bool(args.get("overwrite", False))
    elif name == "edit_file":
        action["change"] = (
            f"替换片段（old → new）：\n- {str(args.get('old_text') or '')[:200]}\n"
            f"+ {str(args.get('new_text') or '')[:200]}"
        )
    else:
        action["change"] = str(args)[:200]
    return action


async def make_plan(state: CodingState, config: RunnableConfig) -> dict[str, Any]:
    """planner 的包装节点：产出计划，并把本次运行的模式写进 State。"""
    out = await planner(state, config)
    out["allow_write"] = _allow_write(config)
    out["attempts"] = int(state.get("attempts") or 0)
    out["trajectory_started_at"] = state.get("trajectory_started_at") or utc_now()
    return out


async def call_model(state: CodingState, config: RunnableConfig) -> dict[str, Any]:
    """coder 节点：带着计划思考，并决定是否调用工具。"""
    if "model" not in _configurable(config):
        raise ValueError("`model` is required in the configuration")
    model = get_model(_configurable(config).get("model", settings.DEFAULT_MODEL))
    bound_model = model.bind_tools(_allowed_tools(config))

    messages: list[Any] = [SystemMessage(content=SYSTEM_PROMPT)]

    plan = state.get("plan")
    if plan:
        messages.append(
            SystemMessage(
                content=(
                    "以下是本次任务的执行计划（按 order 顺序执行）。"
                    "如需偏离计划，必须先说明原因：\n"
                    + json.dumps(plan, ensure_ascii=False, indent=2)
                )
            )
        )
    if not _allow_write(config):
        messages.append(
            SystemMessage(
                content=(
                    "本次运行**没有写权限**：你不能修改仓库里的任何文件。"
                    "如果需要修改，请给出具体的修改建议（文件路径 + 行号 + 建议内容），"
                    "并说明需要人工授权。"
                )
            )
        )

    messages += state["messages"]
    response = await bound_model.ainvoke(messages)
    return {"messages": [response]}


def should_act(state: CodingState) -> Literal["tools", "tester", "end"]:
    """coder 之后：还有工具调用就继续执行；否则进入测试（自我修复模式）或结束。"""
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return "tester" if state.get("allow_write") else "end"


async def act(state: CodingState, config: RunnableConfig) -> dict[str, Any]:
    """工具执行节点（自己实现的 dispatcher + 人工审批闸门）。

    为什么不用 ToolNode：工具白名单要**按运行模式动态决定**。这里对每个 tool_call
    再校验一次"当前模式是否允许"，越权调用只会得到一条 ERROR 的 ToolMessage，
    而不是真的执行——这就是"不绑给模型"之外的第二道闸门。

    HITL（阶段 13）：如果本批里有写操作、且 `require_approval=True`（默认），
    先 `interrupt()` 暂停等人批准，**批准之后才开始执行**。
    关键细节：LangGraph 在 resume 时会**从头重跑本节点**，所以审批必须在任何副作用
    之前完成——否则被批准的那批写操作会被执行两次。
    """
    allowed = {t.name for t in _allowed_tools(config)}
    last = state["messages"][-1]
    calls = getattr(last, "tool_calls", None) or []

    # ---- 第一遍：只做判断，不产生任何副作用 ----
    pending = [c for c in calls if c.get("name") in WRITE_TOOL_NAMES and c.get("name") in allowed]
    decisions: dict[str, bool] = {}
    if pending and _require_approval(config):
        answer = interrupt(
            {
                "type": "approval_request",
                "question": (
                    "以下操作会修改仓库文件，是否批准执行？"
                    "回复「批准」继续，回复「拒绝」放弃本次修改。"
                ),
                "actions": [_describe_action(state, call) for call in pending],
                "read_only_tools_are_not_asked": True,
            }
        )
        approved = _is_approved(answer)
        decisions = {str(c.get("id", "")): approved for c in pending}

    # ---- 第二遍：执行（此时审批已完成） ----
    results: list[ToolMessage] = []
    approval_records: list[dict[str, Any]] = []
    for call in calls:
        name = call.get("name", "")
        call_id = str(call.get("id", ""))
        tool = _TOOL_BY_NAME.get(name)
        if call_id in decisions:
            approved = decisions[call_id]
            approval_records.append(
                {
                    "tool": name,
                    "path": str((call.get("args") or {}).get("path") or ""),
                    "approved": approved,
                    "reason": _plan_reason(state, str((call.get("args") or {}).get("path") or "")),
                }
            )
            if not approved:
                results.append(
                    ToolMessage(
                        content=(
                            "ERROR: 用户拒绝执行这次写入，文件未被修改。"
                            "请停止修改，改为说明你的建议（文件路径 + 行号 + 建议内容）"
                            "或询问用户希望怎么做。"
                        ),
                        tool_call_id=call_id,
                        name=name,
                    )
                )
                continue
        if tool is None:
            content = f"ERROR: 未知工具: {name}"
        elif name not in allowed:
            content = (
                f"ERROR: 当前模式不允许调用工具 {name}"
                f"（allow_write={_allow_write(config)}）"
            )
        else:
            try:
                content = str(tool.invoke(call.get("args") or {}))
            except Exception as e:
                content = f"ERROR: {e}"
        results.append(ToolMessage(content=content, tool_call_id=call_id, name=name))

    out: dict[str, Any] = {"messages": results}
    if approval_records:
        out["approvals"] = [*(state.get("approvals") or []), *approval_records]
    return out


def _parse_test_result(text: str) -> dict[str, Any]:
    """把 run_tests 的结构化文本解析成 dict（下游条件边要用它判断）。"""
    result: dict[str, Any] = {}
    output: list[str] = []
    in_output = False
    for line in text.splitlines():
        if in_output:
            output.append(line)
            continue
        if line.startswith("output:"):
            in_output = True
            continue
        for key in ("command", "exit_code", "status", "passed", "summary"):
            prefix = f"{key}: "
            if line.startswith(prefix):
                result[key] = line[len(prefix) :].strip()
                break
    result["output"] = "\n".join(output)
    if "exit_code" in result:
        try:
            result["exit_code"] = int(result["exit_code"])
        except (TypeError, ValueError):
            pass
    result["passed"] = result.get("passed") == "true"
    result.setdefault("status", "error")
    return result


def _derive_test_path(plan: dict[str, Any]) -> str:
    """从计划的 verification 里挑一个真实存在的测试路径（挑不到就返回空 = 跑全部）。"""
    for command in plan.get("verification") or []:
        for token in str(command).split():
            if token.startswith("-") or token in {"python", "-m", "pytest", "uv", "run", "&&"}:
                continue
            if "/" in token or token.endswith(".py"):
                if (PROJECT_ROOT / token).exists():
                    return token
    return ""


async def tester(state: CodingState, config: RunnableConfig) -> dict[str, Any]:
    """测试节点：真实跑 pytest，把结构化结果与重试计数写进 State。"""
    conf = _configurable(config)
    attempts = int(state.get("attempts") or 0) + 1
    test_path = str(conf.get("test_path") or "") or _derive_test_path(state.get("plan") or {})
    timeout = conf.get("test_timeout", 120)
    raw = str(run_tests.invoke({"path": test_path, "timeout": timeout}))
    return {"test_result": _parse_test_result(raw), "attempts": attempts}


def check_test(state: CodingState) -> Literal["pass", "retry", "giveup"]:
    """测试之后：通过就结束；没通过且还有额度就重试；额度用完就放弃。"""
    result = state.get("test_result") or {}
    if result.get("status") == "passed":
        return "pass"
    if int(state.get("attempts") or 0) >= MAX_RETRIES:
        return "giveup"
    return "retry"


async def debugger(state: CodingState, config: RunnableConfig) -> dict[str, Any]:
    """把失败信息整理成"给 coder 的修复指令"，并附上当前 diff 让改动可见。"""
    result = state.get("test_result") or {}
    attempts = int(state.get("attempts") or 0)
    diff = str(git_diff.invoke({})) if _allow_write(config) else "（无写权限，未取 diff）"
    content = (
        f"第 {attempts} 次尝试的测试**没有通过**，需要你继续修复。\n"
        f"测试命令：{result.get('command')}\n"
        f"状态：{result.get('status')}（exit_code={result.get('exit_code')}）\n"
        f"摘要：{result.get('summary')}\n\n"
        f"失败输出（已截断）：\n{(result.get('output') or '')[:4000]}\n\n"
        f"当前工作区改动：\n{diff[:2000]}\n\n"
        "请先定位失败原因（引用具体的 `文件名:行号`），再用 edit_file 做最小修复；"
        "不要重写整个文件，也不要改动与失败无关的代码。"
    )
    return {"messages": [HumanMessage(content=content)]}


async def giveup(state: CodingState, config: RunnableConfig) -> dict[str, Any]:
    """重试额度用完：明确报告"没完成"，绝不假装成功。"""
    result = state.get("test_result") or {}
    content = (
        f"[FAIL] 已尝试 {MAX_RETRIES} 次仍未通过测试，停止自动修复。\n"
        f"测试命令：{result.get('command')}\n"
        f"状态：{result.get('status')}（exit_code={result.get('exit_code')}）\n"
        f"摘要：{result.get('summary')}\n\n"
        f"最后一次失败输出（已截断）：\n{(result.get('output') or '')[:1500]}\n\n"
        "结论：本次任务**没有完成**，需要人工介入或更明确的指示。"
    )
    return {"messages": [AIMessage(content=content)]}


async def finalize_trajectory(state: CodingState, config: RunnableConfig) -> dict[str, Any]:
    """所有终态的统一出口：记录成功、失败和只读任务，绝不让记录失败掩盖任务结果。"""
    record = build_trajectory(state, config)
    try:
        append_trajectory(record, trajectory_path(config))
    except OSError as exc:
        # 任务已经完成；观测数据写入失败不能反过来让用户得到一次失败任务。
        record["persistence_error"] = f"{type(exc).__name__}: {exc}"
    return {"trajectory": record}


def build_graph(checkpointer: Any | None = None):
    """建图：planner → coder ↔ tools，并在放开写权限时接上 tester/debugger 闭环。

    checkpointer 必须传：HITL 的 interrupt() 需要它来持久化"暂停点"，
    否则图无法恢复（服务端在启动时会给注册表里的图挂上 SQLite checkpointer）。
    """
    graph = StateGraph(CodingState)

    graph.add_node("planner", make_plan)
    graph.add_node("coder", call_model)
    graph.add_node("tools", act)
    graph.add_node("tester", tester)
    graph.add_node("debugger", debugger)
    graph.add_node("giveup", giveup)
    graph.add_node("reviewer", reviewer)
    graph.add_node("finalize_trajectory", finalize_trajectory)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "coder")
    graph.add_conditional_edges(
        "coder", should_act, {"tools": "tools", "tester": "tester", "end": "finalize_trajectory"}
    )
    graph.add_edge("tools", "coder")
    # 测试通过后不直接 END：先交给 Reviewer 做独立裁决（阶段 12）
    graph.add_conditional_edges(
        "tester", check_test, {"pass": "reviewer", "retry": "debugger", "giveup": "giveup"}
    )
    graph.add_edge("debugger", "coder")
    graph.add_edge("giveup", "finalize_trajectory")
    graph.add_edge("reviewer", "finalize_trajectory")
    graph.add_edge("finalize_trajectory", END)

    return graph.compile(checkpointer=checkpointer)


# agents.py 注册表需要的是一个已编译的图对象（和 rag_assistant 一样的约定）
coding_agent = build_graph()


if __name__ == "__main__":
    import asyncio

    async def main():
        graph = build_graph()
        question = "这个项目的 FastAPI 服务入口在哪里？"
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=question)]},
            config={"configurable": {"model": settings.DEFAULT_MODEL}},
        )
        print(result["messages"][-1].content)

    asyncio.run(main())
