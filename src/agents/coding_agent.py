"""Coding Agent：能查看代码仓库、并按计划行事的 Agent。

图结构（阶段 9 之后）：

    START → planner → coder → (有 tool_calls ? tools → coder : END)

两个关键设计：
  1) planner 先产出**结构化计划**并写进 State 的 `plan` 字段——计划进 State 才能被
     后续节点读取、校验、执行；只打印给用户就只是个进度条。
  2) coder 每次调用都把 `plan` 作为上下文带上，并被告知"如需偏离先说明原因"。
"""

import json
from typing import Any, Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from agents.code_tools import git_diff, list_files, read_file, search_code
from agents.coding_planner import planner
from agents.test_tools import run_tests
from core import get_model, settings

# 说明：这里刻意只接"只读"工具。write_file / edit_file 属于写权限，
# 按 v3 §13 / §37 的顺序，等 HITL（阶段 13）就位后再交给模型。
TOOLS = [search_code, read_file, list_files, git_diff, run_tests]


class CodingState(MessagesState):
    """比 MessagesState 多一个 plan：规划器的产出，供 coder 与后续节点读取。"""

    plan: dict[str, Any]

SYSTEM_PROMPT = """你是一个代码助手，工作在一个 Python 项目仓库里。

工作规则：
1. 先定位、再精读：用 search_code 按关键词 / 函数名 / 类名搜索，拿到 `路径:行号`，
   再用 read_file 读那几行的上下文。只有在完全不知道该搜什么时，才先用 list_files
   看看仓库结构。不要凭记忆或猜测回答。
2. 你的每个结论都必须来自你真正读到的文件内容。
3. 回答时必须给出证据：文件路径 + 行号，例如 src/run_service.py:36。
4. search_code 返回 no matches 时，换关键词、换大小写策略或放宽 path_glob 再试一次，
   不要一次搜不到就放弃，也不要转为盲读整个仓库。
5. 涉及"改了什么 / 有哪些改动"的问题时，用 git_diff 读真实差异，不要凭猜测回答。
6. 涉及"能不能跑通 / 测试是否通过"的问题时，用 run_tests 真实执行 pytest，
   并按返回的 status / summary 回答；不要用"应该没问题"这类没有依据的说法。
7. 只讨论这个仓库里的内容。如果文件不存在或没有权限，如实说明，
   不要编造文件内容。
"""


async def call_model(state: CodingState, config: RunnableConfig) -> dict:
    """coder 节点：带着计划思考，并决定是否调用工具。"""
    # 从运行时配置中动态获取模型，支持前端切换模型
    model_name = config["configurable"].get("model", settings.DEFAULT_MODEL)
    model = get_model(model_name)

    bound_model = model.bind_tools(TOOLS)
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    # 把 planner 产出的计划作为上下文喂给 coder：
    # 计划只有被"使用"，才算真的进了控制链路。
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
    messages += state["messages"]

    # 异步调用，避免阻塞整个服务的事件循环
    response = await bound_model.ainvoke(messages)
    return {"messages": [response]}


def should_use_tools(state: CodingState) -> Literal["tools", "end"]:
    """条件边：判断模型是否发出了工具调用指令。"""
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return "end"


def build_graph():
    """建图：planner → coder <-> tools。"""
    graph = StateGraph(CodingState)

    graph.add_node("planner", planner)
    graph.add_node("coder", call_model)
    graph.add_node("tools", ToolNode(TOOLS))

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "coder")
    graph.add_conditional_edges("coder", should_use_tools, {"tools": "tools", "end": END})
    graph.add_edge("tools", "coder")

    return graph.compile()


# agents.py 注册表需要的是一个已编译的图对象（和 rag_assistant 一样的约定）
coding_agent = build_graph()


if __name__ == "__main__":
    import asyncio

    async def main():
        graph = build_graph()
        question = "这个项目的 FastAPI 服务入口在哪里？它做了什么？"
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=question)]},
            config={"configurable": {"model": settings.DEFAULT_MODEL}},
        )
        print(result["messages"][-1].content)

    asyncio.run(main())
