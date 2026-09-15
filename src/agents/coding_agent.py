"""Coding Agent：能自己查看代码仓库并回答问题的 Agent。

与 rag_assistant.py 的关系：图结构完全相同（model <-> tools 循环 + 一条条件边），
区别只在两点：
  1) 工具从 Database_Search 换成 list_files / read_file（看代码，而不是看手册）；
  2) 提示词要求"先查再答、结论必须带文件路径 + 行号"。

源文件保留在 study_test11/coding_agent.py，这里是接入服务用的正式版本。
"""

from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from agents.code_tools import git_diff, list_files, read_file, search_code
from core import get_model, settings

# 说明：这里刻意只接"只读"工具。write_file / edit_file 属于写权限，
# 按 v3 §13 / §37 的顺序，等 HITL（阶段 13）就位后再交给模型。
TOOLS = [search_code, read_file, list_files, git_diff]

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
6. 只讨论这个仓库里的内容。如果文件不存在或没有权限，如实说明，
   不要编造文件内容。
"""


async def call_model(state: MessagesState, config: RunnableConfig) -> dict:
    """异步模型节点：负责思考并决定是否调用工具。"""
    # 从运行时配置中动态获取模型，支持前端切换模型
    model_name = config["configurable"].get("model", settings.DEFAULT_MODEL)
    model = get_model(model_name)

    bound_model = model.bind_tools(TOOLS)
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]

    # 异步调用，避免阻塞整个服务的事件循环
    response = await bound_model.ainvoke(messages)
    return {"messages": [response]}


def should_use_tools(state: MessagesState) -> Literal["tools", "end"]:
    """条件边：判断模型是否发出了工具调用指令。"""
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return "end"


def build_graph():
    """建图：model <-> tools 循环 + 一条条件边。"""
    graph = StateGraph(MessagesState)

    graph.add_node("model", call_model)
    graph.add_node("tools", ToolNode(TOOLS))

    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", should_use_tools, {"tools": "tools", "end": END})
    graph.add_edge("tools", "model")

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
