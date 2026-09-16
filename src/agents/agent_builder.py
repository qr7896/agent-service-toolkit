"""Agent Builder 的纯逻辑层（阶段 22 第三块）。

界面本身只是数据的编辑器，所以这里把"能编辑什么、编辑后怎么校验、写到哪"抽成不依赖
Streamlit 的函数：这样界面薄、逻辑可测，也不会出现"只有点开页面才能验证"的死角。

只做最必要的四件事：列出配置、读一份配置、保存一份配置（保存前校验工具白名单）、
删除一份配置。所有写入都限定在 `config/agents/` 目录内。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agents.agent_config import AgentConfig, AgentConfigError, CONFIG_SUFFIXES

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = PROJECT_ROOT / "config" / "agents"


def list_configs(directory: Path = AGENTS_DIR) -> list[dict[str, Any]]:
    """列出目录里所有 Agent 配置（含文件名），坏配置也列出来并标上错误原因。"""
    items: list[dict[str, Any]] = []
    if not directory.exists():
        return items
    for path in sorted(directory.iterdir()):
        if path.suffix not in CONFIG_SUFFIXES or not path.is_file():
            continue
        entry: dict[str, Any] = {"file": path.name}
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            entry["config"] = data if isinstance(data, dict) else {}
        except yaml.YAMLError as exc:
            entry["error"] = f"解析失败：{exc}"
        items.append(entry)
    return items


def save_config(data: dict[str, Any], known_tools: set[str], directory: Path = AGENTS_DIR) -> Path:
    """保存（新建或覆盖）一份配置。写盘前必须通过同一套校验。"""
    key = str(data.get("key") or "").strip()
    if not key:
        raise AgentConfigError("缺少 `key`")
    # 先校验再落盘：不让半成品配置进入 config/ 目录，避免下次启动直接崩
    unknown = sorted(set(data.get("tools") or []) - known_tools)
    if unknown:
        raise AgentConfigError(f"未知工具 {unknown}；可用：{sorted(known_tools)}")
    try:
        AgentConfig.model_validate({**data, "key": key})
    except Exception as exc:  # pydantic.ValidationError
        raise AgentConfigError(f"配置不合法：{exc}") from exc

    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{key}.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "key": key,
                "description": data.get("description", ""),
                "system_prompt": data.get("system_prompt", ""),
                "tools": list(data.get("tools") or []),
                "max_tool_rounds": int(data.get("max_tool_rounds") or 6),
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def delete_config(key: str, directory: Path = AGENTS_DIR) -> bool:
    """删除一份配置。只删目录内由 key 推出的文件名，不接受任意路径。"""
    safe = "".join(ch for ch in key if ch.isalnum() or ch in "-_")
    if not safe or safe != key:
        raise AgentConfigError(f"key `{key}` 含有非法字符")
    path = directory / f"{safe}.yaml"
    if not path.is_file():
        return False
    path.unlink()
    return True


__all__ = ["AGENTS_DIR", "delete_config", "list_configs", "save_config"]
