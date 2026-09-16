"""Agent 工作流编排（阶段 22 第二块）。

有了“可配置的 Agent”之后，下一步才是把它们串起来：一个 Agent 的输出成为下一个的输入。
这里刻意只做**线性串联**这一种最小编排，不做分支、不做并行、不做条件跳转——那三样都
需要先有可靠的失败传播与回滚设计，现在做只会得到一个看起来很强、实际上很难解释的图。

输入模板占位符：
  `{input}`    —— 用户最初的需求（每一步都能拿到）
  `{previous}` —— 上一步的输出（第一步没有上一步，会得到空串）

两条校验：引用的 Agent 必须存在；步骤不能为空。与 Agent 配置一样，错了就在加载时抛错。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from pydantic import BaseModel, Field, ValidationError

from agents.agent_config import AgentConfigError


class WorkflowStep(BaseModel):
    agent: str = Field(description="已有 Agent 的 key")
    name: str = Field(default="", description="这一步的显示名，留空则用 agent key")
    input_template: str = Field(default="{input}", description="支持 {input} / {previous}")


class WorkflowConfig(BaseModel):
    key: str
    description: str = ""
    steps: list[WorkflowStep] = Field(default_factory=list)


class WorkflowState(MessagesState):
    step_outputs: list[str]
    workflow_input: str


def render_template(template: str, user_input: str, previous: str) -> str:
    """只替换两个已知占位符；不用 str.format()，避免模板里的花括号被当成字段。"""
    return template.replace("{input}", user_input).replace("{previous}", previous)


def build_workflow(config: WorkflowConfig, agent_graphs: dict[str, Any]):
    """把工作流编译成线性图：START -> step_1 -> step_2 -> ... -> END。"""
    if not config.steps:
        raise AgentConfigError(f"工作流 `{config.key}` 至少要有一步")
    unknown = sorted({step.agent for step in config.steps} - set(agent_graphs))
    if unknown:
        raise AgentConfigError(
            f"工作流 `{config.key}` 引用了不存在的 Agent {unknown}；可用：{sorted(agent_graphs)}"
        )

    def make_step(step: WorkflowStep):
        agent_graph = agent_graphs[step.agent]

        async def run_step(state: WorkflowState, run_config: RunnableConfig | None = None) -> dict:
            outputs = list(state.get("step_outputs") or [])
            previous = outputs[-1] if outputs else ""
            prompt = render_template(step.input_template, state.get("workflow_input") or "", previous)
            result = await agent_graph.ainvoke(
                {"messages": [HumanMessage(content=prompt)]}, run_config or {}
            )
            text = str(result["messages"][-1].content)
            return {"messages": [AIMessage(content=text)], "step_outputs": [*outputs, text]}

        return run_step

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
    if not config.steps:
        raise AgentConfigError(f"{path.name}: `steps` 不能为空")
    if known_agents is not None:
        unknown = sorted({step.agent for step in config.steps} - known_agents)
        if unknown:
            raise AgentConfigError(
                f"{path.name}: 引用了不存在的 Agent {unknown}；可用：{sorted(known_agents)}"
            )
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
    "load_workflow_config",
    "load_workflow_configs",
    "render_template",
]
