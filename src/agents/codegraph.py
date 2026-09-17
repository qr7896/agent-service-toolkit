"""CodeGraph 适配层（doc 03 §4）。

CodeGraph 是**基础设施**：成熟就复用，不重写。它对外提供的典型结构化动作是
`symbol_search / get_ai_context / get_callers / get_callees / analyze_impact / find_related_tests`，
本项目只依赖这组语义，不依赖它的具体传输方式。

三种后端，按优先级：

  1. **CLI**：设置 `CODEGRAPH_CLI` 指向可执行文件，调用 `<cli> <tool> --json '<args>'`；
  2. **MCP**：设置 `CODEGRAPH_MCP_URL`（HTTP 端点），POST JSON-RPC；
  3. **回退**：都没有时抛 `CodeGraphUnavailable`，由 `code_intel` 退回本地 ast 实现。

关键点：**回退不是静默降级**。`probe()` 会说明当前用的是哪种后端以及为什么，
轨迹里也会记录实际后端，避免"以为在用 CodeGraph、其实在用本地索引"这类说不清的事。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any

TOOLS = (
    "symbol_search",
    "get_ai_context",
    "get_callers",
    "get_callees",
    "analyze_impact",
    "find_related_tests",
    "symbols_in_file",
)
TIMEOUT_SECONDS = 60


class CodeGraphUnavailable(RuntimeError):
    """没有可用的 CodeGraph 后端（不是错误，是回退信号）。"""


def _cli_path() -> str:
    return str(os.getenv("CODEGRAPH_CLI") or "").strip()


def _mcp_url() -> str:
    return str(os.getenv("CODEGRAPH_MCP_URL") or "").strip()


def probe() -> dict[str, Any]:
    """报告当前后端。没有配置任何后端时返回 reason，方便上层决定是否回退。"""
    cli = _cli_path()
    if cli:
        resolved = shutil.which(cli) or cli
        if os.path.exists(resolved):
            return {"available": True, "backend": "cli", "target": resolved}
        return {"available": False, "backend": "", "reason": f"CODEGRAPH_CLI 指向的路径不存在：{cli}"}
    url = _mcp_url()
    if url:
        return {"available": True, "backend": "mcp", "target": url}
    return {"available": False, "backend": "", "reason": "未配置 CODEGRAPH_CLI / CODEGRAPH_MCP_URL"}


def call(tool: str, **arguments: Any) -> str:
    """调用 CodeGraph 工具，返回文本结果。后端不可用时抛 CodeGraphUnavailable。"""
    if tool not in TOOLS:
        raise ValueError(f"unsupported CodeGraph tool: {tool}")
    status = probe()
    if not status["available"]:
        raise CodeGraphUnavailable(status["reason"])

    if status["backend"] == "cli":
        payload = json.dumps(arguments, ensure_ascii=False)
        try:
            proc = subprocess.run(
                [str(status["target"]), tool, "--json", payload],
                capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise CodeGraphUnavailable(f"CLI 调用失败：{exc}") from exc
        if proc.returncode != 0:
            raise CodeGraphUnavailable(f"CLI 返回 {proc.returncode}：{proc.stderr.strip()[:200]}")
        return proc.stdout.strip()

    # MCP：用最小 JSON-RPC 载荷，避免引入额外客户端依赖
    try:
        import urllib.request

        request = urllib.request.Request(
            str(status["target"]),
            data=json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                 "params": {"name": tool, "arguments": arguments}},
                ensure_ascii=False,
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - 任何网络/协议问题都当作"不可用"回退
        raise CodeGraphUnavailable(f"MCP 调用失败：{exc}") from exc
    result = body.get("result") if isinstance(body, dict) else None
    if isinstance(result, dict) and "content" in result:
        parts = [item.get("text", "") for item in result["content"] if isinstance(item, dict)]
        return "\n".join(part for part in parts if part)
    return json.dumps(result if result is not None else body, ensure_ascii=False)


__all__ = ["TOOLS", "CodeGraphUnavailable", "call", "probe"]
