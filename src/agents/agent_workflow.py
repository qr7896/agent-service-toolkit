"""Agent 工作流编排（阶段 22）。

三种模式，覆盖"多 Agent 协同"的三种基本形态：

  sequential  上一步的输出成为下一步的输入（链式，最常用）
  parallel    所有步骤拿到同一个输入、并行执行，输出汇总给下游
  router      由一个 supervisor 模型在候选 Agent 中**选一个**执行

为什么不做带条件跳转的复杂图：编排的难点不在"怎么连"，而在"出错时怎么办"。
上面三种模式的失败语义都只有一句话能说清（当前步失败就整条停），复杂图不是。

输入模板占位符：
  `{input}`    —— 用户最初的需求（每一步都能拿到）
  `{previous}` —— 上一步/汇总后的输出（第一步没有上一步，会得到空串）

所有引用的 Agent 必须存在；配置错误一律在加载时抛错。
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Literal

import yaml
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from pydantic import BaseModel, Field, ValidationError

from agents.agent_config import AgentConfigError
from core import get_model, settings


class WorkflowStep(BaseModel):
    agent: str = Field(description="已有 Agent 的 key")
    name: str = Field(default="", description="这一步的显示名，留空则用 agent key")
    input_template: str = Field(default="{input}", description="支持 {input} / {previous}")


class WorkflowConfig(BaseModel):
    key: str
    description: str = ""
    mode: Literal["sequential", "parallel", "router"] = "sequential"
    steps: list[WorkflowStep] = Field(default_factory=list)
    candidates: list[str] = Field(default_factory=list, description="router 模式的候选 Agent")
    routing_prompt: str = Field(default="", description="router 模式交给 supervisor 的选人规则")


class WorkflowState(MessagesState):
    step_outputs: list[str]
    workflow_input: str
    chosen: str


def render_template(template: str, user_input: str, previous: str) -> str:
    """只替换两个已知占位符；不用 str.format()，避免模板里的花括号被当成字段。"""
    return template.replace("{input}", user_input).replace("{previous}", previous)


def user_input(state: dict[str, Any]) -> str:
    """工作流的原始输入。

    优先用显式传入的 `workflow_input`；**缺省时必须能从 messages 里取出来**——
    服务端（`/invoke`）只会传 messages，不会传 workflow_input。第一版漏了这一步，
    结果是"通过服务调用工作流时 Agent 收到空输入"，而且所有打桩验收都发现不了，
    因为测试里总是显式传了 workflow_input（真实运行才发现）。
    """
    provided = state.get("workflow_input")
    if provided:
        return str(provided)
    for message in reversed(state.get("messages") or []):
        if message.__class__.__name__ == "HumanMessage":
            return str(getattr(message, "content", "") or "")
    return ""


def referenced_agents(config: WorkflowConfig) -> list[str]:
    names = [step.agent for step in config.steps] or list(config.candidates)
    return names


def validate_workflow(config: WorkflowConfig, agent_graphs: dict[str, Any]) -> None:
    """加载与构建共用同一套校验，避免出现"加载过了但构建时才炸"。"""
    if config.mode == "router":
        if not config.candidates:
            raise AgentConfigError(f"工作流 `{config.key}`（router）必须给出 candidates")
        if not config.routing_prompt.strip():
            raise AgentConfigError(f"工作流 `{config.key}`（router）必须给出 routing_prompt")
    elif not config.steps:
        raise AgentConfigError(f"工作流 `{config.key}` 至少要有一步")
    if config.mode == "router" and config.steps:
        raise AgentConfigError(f"工作流 `{config.key}`（router）用 candidates 指定候选，不写 steps")
    unknown = sorted(set(referenced_agents(config)) - set(agent_graphs))
    if unknown:
        raise AgentConfigError(
            f"工作流 `{config.key}` 引用了不存在的 Agent {unknown}；可用：{sorted(agent_graphs)}"
        )


def _step_runner(step: WorkflowStep, agent_graph: Any):
    async def run_step(state: WorkflowState, run_config: RunnableConfig | None = None) -> dict:
        outputs = list(state.get("step_outputs") or [])
        previous = outputs[-1] if outputs else ""
        prompt = render_template(step.input_template, user_input(state), previous)
        result = await agent_graph.ainvoke(
            {"messages": [HumanMessage(content=prompt)]}, run_config or {}
        )
        text = str(result["messages"][-1].content)
        return {"messages": [AIMessage(content=text)], "step_outputs": [*outputs, text]}

    return run_step


def _build_sequential(config: WorkflowConfig, agent_graphs: dict[str, Any]):
    def make_step(step: WorkflowStep):
        return _step_runner(step, agent_graphs[step.agent])

    graph = StateGraph(WorkflowState)
    names: list[str] = []
    for index, step in enumerate(config.steps, start=1):
        node = f"step_{index}_{step.name or step.agent}"
        graph.add_node(node, make_step(step))
        names.append(node)
    graph.add_edge(START, names[0])
    for left, right in zip(names, names[1:]):
        graph.add_edge(left, right)
    graph.add_edge(names[-1], END)
    return graph.compile()


def _build_parallel(config: WorkflowConfig, agent_graphs: dict[str, Any]):
    """并行：所有步骤拿同一个输入同时跑，输出按声明顺序汇总。

    用一个节点包住 gather，而不是把图摊成扇出扇入——这样失败语义保持"任一失败即整条失败"，
    不会出现"三个分支成了两个、调用方还得自己判断完整性"的模糊状态。
    """

    async def run_all(state: WorkflowState, run_config: RunnableConfig | None = None) -> dict:
        requirement = user_input(state)
        prompts = [
            render_template(step.input_template, requirement, requirement) for step in config.steps
        ]
        results = await asyncio.gather(
            *[
                agent_graphs[step.agent].ainvoke(
                    {"messages": [HumanMessage(content=prompt)]}, run_config or {}
                )
                for step, prompt in zip(config.steps, prompts)
            ]
        )
        outputs = [str(result["messages"][-1].content) for result in results]
        joined = "\n\n".join(
            f"[{step.name or step.agent}]\n{text}" for step, text in zip(config.steps, outputs)
        )
        return {"messages": [AIMessage(content=joined)], "step_outputs": outputs}

    graph = StateGraph(WorkflowState)
    graph.add_node("parallel", run_all)
    graph.add_edge(START, "parallel")
    graph.add_edge("parallel", END)
    return graph.compile()


def make_router_node(config: WorkflowConfig):
    """supervisor 选人节点：让模型在候选里挑一个，解析不出就退回第一个候选。

    解析结果只认候选名单里的 key（用子串匹配），避免模型自由发挥出一个不存在的 Agent。
    """

    async def route(state: WorkflowState, run_config: RunnableConfig | None = None) -> dict:
        conf = (run_config or {}).get("configurable") or {}
        model = get_model(conf.get("model") or settings.DEFAULT_MODEL)
        prompt = (
            f"{config.routing_prompt}\n\n"
            f"候选（必须原样回复其中一个 key）：{', '.join(config.candidates)}\n\n"
            f"用户需求：{user_input(state)}"
        )
        answer = str(getattr(await model.ainvoke([HumanMessage(content=prompt)]), "content", "") or "")
        chosen = next((name for name in config.candidates if name in answer), config.candidates[0])
        return {
            "chosen": chosen,
            "messages": [AIMessage(content=f"[router] 选择 {chosen}")],
        }

    return route


def _build_router(config: WorkflowConfig, agent_graphs: dict[str, Any]):
    graph = StateGraph(WorkflowState)
    graph.add_node("route", make_router_node(config))
    graph.add_edge(START, "route")
    mapping: dict[str, str] = {}
    for name in config.candidates:
        node = f"agent_{name}"
        graph.add_node(
            node, _step_runner(WorkflowStep(agent=name, input_template="{input}"), agent_graphs[name])
        )
        mapping[name] = node
        graph.add_edge(node, END)
    graph.add_conditional_edges("route", lambda state: state.get("chosen") or config.candidates[0], mapping)
    return graph.compile()


def build_workflow(config: WorkflowConfig, agent_graphs: dict[str, Any]):
    """按 mode 编译工作流。三种模式对外都只是一个普通 Agent 图。"""
    validate_workflow(config, agent_graphs)
    if config.mode == "parallel":
        return _build_parallel(config, agent_graphs)
    if config.mode == "router":
        return _build_router(config, agent_graphs)
    return _build_sequential(config, agent_graphs)


def load_workflow_config(path: Path, known_agents: set[str] | None = None) -> WorkflowConfig:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise AgentConfigError(f"{path.name}: 解析失败：{exc}") from exc
    if not isinstance(data, dict):
        raise AgentConfigError(f"{path.name}: 顶层必须是键值对象")
    if not str(data.get("key") or "").strip():
        raise AgentConfigError(f"{path.name}: 缺少必填字段 `key`")
    try:
        config = WorkflowConfig.model_validate(data)
    except ValidationError as exc:
        first = exc.errors()[0]
        field = ".".join(str(part) for part in first.get("loc", ()))
        raise AgentConfigError(f"{path.name}: 字段 `{field}` 不合法：{first.get('msg')}") from exc
    if known_agents is not None:
        try:
            validate_workflow(config, {name: None for name in known_agents})
        except AgentConfigError as exc:
            raise AgentConfigError(f"{path.name}: {exc}") from exc
    else:
        validate_workflow(config, {**{s.agent: None for s in config.steps},
                                   **{c: None for c in config.candidates}})
    return config


def load_workflow_configs(
    directory: Path, known_agents: set[str] | None = None
) -> list[WorkflowConfig]:
    if not directory.exists():
        return []
    configs: list[WorkflowConfig] = []
    seen: dict[str, str] = {}
    for path in sorted(directory.iterdir()):
        if path.suffix not in {".yaml", ".yml"} or not path.is_file():
            continue
        config = load_workflow_config(path, known_agents)
        if config.key in seen:
            raise AgentConfigError(f"{path.name}: key `{config.key}` 与 {seen[config.key]} 重复")
        seen[config.key] = path.name
        configs.append(config)
    return configs


__all__ = [
    "WorkflowConfig",
    "WorkflowState",
    "WorkflowStep",
    "build_workflow",
    "make_router_node",
    "load_workflow_config",
    "load_workflow_configs",
    "render_template",
    "referenced_agents",
    "user_input",
    "validate_workflow",
]
