import logging
import os
from dataclasses import dataclass
from pathlib import Path

from langgraph.graph.state import CompiledStateGraph
from langgraph.pregel import Pregel

from agents.agent_config import AgentConfigError, load_agent_configs
from agents.agent_workflow import build_workflow, load_workflow_configs, referenced_agents
from agents.bg_task_agent.bg_task_agent import bg_task_agent
from agents.chatbot import chatbot
from agents.code_tools import git_diff, list_files, read_file, search_code
from agents.command_agent import command_agent
from agents.coding_agent import coding_agent
from agents.declarative_agent import build_declarative_agent
from agents.github_mcp_agent.github_mcp_agent import github_mcp_agent
from agents.interrupt_agent import interrupt_agent
from agents.knowledge_base_agent import kb_agent
from agents.langgraph_supervisor_agent import langgraph_supervisor_agent
from agents.langgraph_supervisor_hierarchy_agent import langgraph_supervisor_hierarchy_agent
from agents.lazy_agent import LazyLoadingAgent
from agents.rag_assistant import rag_assistant
from agents.research_assistant import research_assistant
from schema import AgentInfo

DEFAULT_AGENT = "research-assistant"

logger = logging.getLogger(__name__)

# 可配置 Agent 目前只开放只读工具：平台化的第一版不把写权限交给配置文件。
CONFIGURABLE_TOOLS = {
    "search_code": search_code,
    "read_file": read_file,
    "list_files": list_files,
    "git_diff": git_diff,
}
CONFIG_AGENTS_DIR = Path(__file__).resolve().parents[2] / "config" / "agents"
WORKFLOWS_DIR = Path(__file__).resolve().parents[2] / "config" / "workflows"

# Type alias to handle LangGraph's different agent patterns
# - @entrypoint functions return Pregel
# - StateGraph().compile() returns CompiledStateGraph
AgentGraph = CompiledStateGraph | Pregel  # What get_agent() returns (always loaded)
AgentGraphLike = CompiledStateGraph | Pregel | LazyLoadingAgent  # What can be stored in registry


@dataclass
class Agent:
    description: str
    graph_like: AgentGraphLike


def _configurable_agents() -> dict[str, "Agent"]:
    """把 config/agents/*.yaml 编译成 Agent。

    没配置目录就返回空字典——**不配置等于不存在**，内置 Agent 行为逐字不变。
    配置写错（缺字段 / 未知工具 / key 重名）会直接抛错而不是静默跳过：配置系统里
    静默降级比启动失败更贵，因为你会以为那个 Agent 还在。
    """
    if os.getenv("CONFIG_AGENTS", "1") == "0":
        return {}
    try:
        configs = load_agent_configs(CONFIG_AGENTS_DIR, set(CONFIGURABLE_TOOLS))
    except AgentConfigError as exc:
        logger.error("加载可配置 Agent 失败：%s", exc)
        raise

    loaded: dict[str, Agent] = {}
    for config in configs:
        graph = build_declarative_agent(config, CONFIGURABLE_TOOLS)
        loaded[config.key] = Agent(description=config.description, graph_like=graph)
    return loaded


def _workflow_agents() -> dict[str, "Agent"]:
    """把 config/workflows/*.yaml 编译成 Agent（线性串联已有 Agent）。

    必须在内置与配置型 Agent 都注册完之后再调用——工作流引用的是它们的图。
    延迟加载的 Agent 暂不支持：工作流在启动时就要拿到图，而延迟加载的图那时还没有。
    """
    if os.getenv("CONFIG_AGENTS", "1") == "0":
        return {}
    try:
        # 不在这里校验引用：工作流之间可以互相引用（组合），引用关系在建图阶段统一校验
        configs = load_workflow_configs(WORKFLOWS_DIR)
    except AgentConfigError as exc:
        logger.error("加载工作流失败：%s", exc)
        raise

    # 按依赖顺序建图：一个工作流可以把另一个工作流当成"一个 Agent"来引用，
    # 于是"循环里套并行"这类组合通过**引用**实现，而不需要在 schema 里加嵌套字段。
    graphs: dict[str, AgentGraph] = {}
    for name, agent in agents.items():
        if isinstance(agent.graph_like, LazyLoadingAgent):
            continue  # 延迟加载的图启动时还不存在，不能被引用
        graphs[name] = agent.graph_like

    built: dict[str, Agent] = {}
    pending = list(configs)
    while pending:
        progressed = False
        for config in list(pending):
            if set(referenced_agents(config)) <= set(graphs):
                compiled = build_workflow(config, graphs)
                built[config.key] = Agent(description=config.description, graph_like=compiled)
                graphs[config.key] = compiled
                pending.remove(config)
                progressed = True
        if not progressed:
            raise AgentConfigError(
                "工作流互相引用成环，或引用了未定义的工作流/延迟加载的 Agent："
                f"{sorted(config.key for config in pending)}"
            )
    return built


agents: dict[str, Agent] = {
    "chatbot": Agent(description="A simple chatbot.", graph_like=chatbot),
    "research-assistant": Agent(
        description="A research assistant with web search and calculator.",
        graph_like=research_assistant,
    ),
    "rag-assistant": Agent(
        description="A RAG assistant with access to information in a database.",
        graph_like=rag_assistant,
    ),
    "coding-agent": Agent(
        description="A coding agent that can explore and explain this repository's code.",
        graph_like=coding_agent,
    ),
    "command-agent": Agent(description="A command agent.", graph_like=command_agent),
    "bg-task-agent": Agent(description="A background task agent.", graph_like=bg_task_agent),
    "langgraph-supervisor-agent": Agent(
        description="A langgraph supervisor agent", graph_like=langgraph_supervisor_agent
    ),
    "langgraph-supervisor-hierarchy-agent": Agent(
        description="A langgraph supervisor agent with a nested hierarchy of agents",
        graph_like=langgraph_supervisor_hierarchy_agent,
    ),
    "interrupt-agent": Agent(
        description="An agent the uses interrupts.", graph_like=interrupt_agent
    ),
    "knowledge-base-agent": Agent(
        description="A retrieval-augmented generation agent using Amazon Bedrock Knowledge Base",
        graph_like=kb_agent,
    ),
    "github-mcp-agent": Agent(
        description="A GitHub agent with MCP tools for repository management and development workflows.",
        graph_like=github_mcp_agent,
    ),
}

# 可配置 Agent 与内置 Agent 合并；key 冲突直接报错，不允许悄悄覆盖内置实现。
for _key, _agent in _configurable_agents().items():
    if _key in agents:
        raise AgentConfigError(f"配置里的 key `{_key}` 与内置 Agent 重名，请改名")
    agents[_key] = _agent

for _key, _agent in _workflow_agents().items():
    if _key in agents:
        raise AgentConfigError(f"工作流里的 key `{_key}` 与已有 Agent 重名，请改名")
    agents[_key] = _agent


async def load_agent(agent_id: str) -> None:
    """Load lazy agents if needed."""
    graph_like = agents[agent_id].graph_like
    if isinstance(graph_like, LazyLoadingAgent):
        await graph_like.load()


def get_agent(agent_id: str) -> AgentGraph:
    """Get an agent graph, loading lazy agents if needed."""
    agent_graph = agents[agent_id].graph_like

    # If it's a lazy loading agent, ensure it's loaded and return its graph
    if isinstance(agent_graph, LazyLoadingAgent):
        if not agent_graph._loaded:
            raise RuntimeError(f"Agent {agent_id} not loaded. Call load() first.")
        return agent_graph.get_graph()

    # Otherwise return the graph directly
    return agent_graph


def get_all_agent_info() -> list[AgentInfo]:
    return [
        AgentInfo(key=agent_id, description=agent.description) for agent_id, agent in agents.items()
    ]
