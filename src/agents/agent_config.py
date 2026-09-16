"""可配置 Agent 的数据定义（v5 §41 / 阶段 22）。

这一层要解决的问题是：现在每个 Agent 都是一个写死的 Python 模块（`agents.py` 里的
字典 + 各自的 graph 文件），想改系统提示词、换个工具集合、调模型，都得改代码。
平台化的第一步不是加界面，而是让 Agent 先变成**可校验的数据**：

    key / description / system_prompt / tools / model / max_tool_rounds

三条设计原则：
  - **工具名走白名单**：配置里写错一个工具名必须当场报错，而不是运行时静默少一个能力；
  - **校验失败要指出文件和字段**：配置文件出错时，人需要知道去改哪一行；
  - **不配置就等于不存在**：没有配置文件时，注册表行为与以前逐字一致。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError


class AgentConfigError(ValueError):
    """配置不可用（语法、字段、工具名、重名）。消息里必须带文件与字段。"""


CONFIG_SUFFIXES = {".yaml", ".yml", ".json"}


class AgentConfig(BaseModel):
    key: str = Field(description="Agent 标识，注册表里的键")
    description: str = Field(default="", description="给人看的说明")
    system_prompt: str = Field(default="", description="系统提示词")
    tools: list[str] = Field(default_factory=list, description="允许使用的工具名（白名单）")
    model: str | None = Field(default=None, description="不填则用运行时传入的模型")
    max_tool_rounds: int = Field(default=6, ge=1, le=50, description="工具循环上限")


def _load_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) if path.suffix in {".yaml", ".yml"} else json.loads(text)
    if not isinstance(data, dict):
        raise AgentConfigError(f"{path.name}: 顶层必须是键值对象，实际是 {type(data).__name__}")
    return data


def load_agent_config(path: Path, known_tools: set[str] | None = None) -> AgentConfig:
    """读单个配置文件并校验。任何问题都抛 AgentConfigError，消息里带文件名。"""
    try:
        data = _load_file(path)
    except AgentConfigError:
        raise
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        raise AgentConfigError(f"{path.name}: 解析失败：{exc}") from exc

    for required in ("key", "system_prompt"):
        if not str(data.get(required) or "").strip():
            raise AgentConfigError(f"{path.name}: 缺少必填字段 `{required}`")

    try:
        config = AgentConfig.model_validate(data)
    except ValidationError as exc:
        first = exc.errors()[0]
        field = ".".join(str(part) for part in first.get("loc", ()))
        raise AgentConfigError(f"{path.name}: 字段 `{field}` 不合法：{first.get('msg')}") from exc

    if known_tools is not None:
        unknown = sorted(set(config.tools) - known_tools)
        if unknown:
            raise AgentConfigError(
                f"{path.name}: 未知工具 {unknown}；可用工具：{sorted(known_tools)}"
            )
    return config


def load_agent_configs(
    directory: Path, known_tools: set[str] | None = None
) -> list[AgentConfig]:
    """读目录下所有配置。目录不存在就返回空列表——没配置等于没这层。"""
    if not directory.exists():
        return []
    configs: list[AgentConfig] = []
    seen: dict[str, str] = {}
    for path in sorted(directory.iterdir()):
        if path.suffix not in CONFIG_SUFFIXES or not path.is_file():
            continue
        config = load_agent_config(path, known_tools)
        if config.key in seen:
            raise AgentConfigError(f"{path.name}: key `{config.key}` 与 {seen[config.key]} 重复")
        seen[config.key] = path.name
        configs.append(config)
    return configs


__all__ = [
    "CONFIG_SUFFIXES",
    "AgentConfig",
    "AgentConfigError",
    "load_agent_config",
    "load_agent_configs",
]
