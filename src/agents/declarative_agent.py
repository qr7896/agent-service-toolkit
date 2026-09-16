"""把 AgentConfig 编译成一张可运行的图（阶段 22）。

图结构刻意做得最小，只保留"模型 ↔ 工具"这个通用骨架：

    START → model ──有 tool_calls──→ tools ──┬─ 还有额度 ─→ model
                 └──没有──────────→ END      └─ 额度用完 ─→ END

两个必须守住的点：
  1. **不在"工具还没执行"的状态下结束**：循环上限检查放在 tools 之后。如果在 model
     之后直接截断，最后一条消息会是"要调工具但没人执行"，这种残缺消息会在后续被
     服务端拒绝（踩坑记录里有同类问题）。
  2. **未知工具不执行**：配置阶段白名单已经拦过一次，运行时再拦一次，越权调用只会
     得到一条 ERROR 的 ToolMessage。
"""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph

from agents.agent_config import AgentConfig
from core import get_model, settings


class DeclarativeState(MessagesState):
    tool_rounds: int


def build_declarative_agent(
    config: AgentConfig,
    tool_registry: dict[str, Any],
    default_model: str | None = None,
):
    """按配置生成图。构建阶段不需要模型可用（模型在节点运行时才解析）。"""
    tools = [tool_registry[name] for name in config.tools]
    max_rounds = config.max_tool_rounds

    async def call_model(
        state: DeclarativeState, run_config: RunnableConfig | None = None
    ) -> dict[str, Any]:
        conf = (run_config or {}).get("configurable") or {}
        model_name = config.model or conf.get("model") or default_model or settings.DEFAULT_MODEL
        model = get_model(model_name)
        bound = model.bind_tools(tools) if tools else model
        messages: list[Any] = []
        if config.system_prompt:
            messages.append(SystemMessage(content=config.system_prompt))
        messages += state["messages"]
        return {"messages": [await bound.ainvoke(messages)]}

    async def run_tools(
        state: DeclarativeState, run_config: RunnableConfig | None = None
    ) -> dict[str, Any]:
        last = state["messages"][-1]
        results: list[ToolMessage] = []
        for call in getattr(last, "tool_calls", None) or []:
            name = call.get("name", "")
            tool = tool_registry.get(name)
            if tool is None:  # 运行时第二道闸门
                content = f"ERROR: 未知工具 {name}"
            else:
                try:
                    content = str(tool.invoke(call.get("args") or {}))
                except Exception as exc:  # 工具失败不该炸掉整张图
                    content = f"ERROR: {exc}"
            results.append(ToolMessage(content=content, tool_call_id=call.get("id", ""), name=name))
        return {"messages": results, "tool_rounds": int(state.get("tool_rounds") or 0) + 1}

    def after_model(state: DeclarativeState) -> Literal["tools", "end"]:
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "tools"
        return "end"

    def after_tools(state: DeclarativeState) -> Literal["model", "end"]:
        if int(state.get("tool_rounds") or 0) >= max_rounds:
            return "end"
        return "model"

    graph = StateGraph(DeclarativeState)
    graph.add_node("model", call_model)
    graph.add_node("tools", run_tools)
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", after_model, {"tools": "tools", "end": END})
    graph.add_conditional_edges("tools", after_tools, {"model": "model", "end": END})
    return graph.compile()


__all__ = ["DeclarativeState", "build_declarative_agent"]
