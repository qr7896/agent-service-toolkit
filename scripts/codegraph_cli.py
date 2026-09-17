"""本项目自带的 CodeGraph 兼容后端（CLI 契约）。

用途：让 `agents/codegraph.py` 的 CLI 后端有一条**真实可用**的实现，而不是只有假 CLI 测试。
它把本仓库的代码智能能力暴露成进程外服务，契约为：

    python scripts/codegraph_cli.py <tool> --json '<arguments-json>'

支持的工具与 `codegraph.TOOLS` 一致；接入第三方 CodeGraph 时只需把 `CODEGRAPH_CLI`
指向它的可执行文件，本项目代码不用改。

注意：本脚本启动时先清掉 `CODEGRAPH_CLI` / `CODEGRAPH_MCP_URL`，强制走本地 ast 实现——
否则 `code_intel` 会优先调用 CodeGraph，而这个 CLI 本身又代理 CodeGraph，形成递归。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

for _key in ("CODEGRAPH_CLI", "CODEGRAPH_MCP_URL"):
    os.environ.pop(_key, None)

from agents import code_intel  # noqa: E402


def main() -> int:
    args = [item for item in sys.argv[1:] if item != "--json"]
    if not args:
        print("usage: codegraph_cli.py <tool> --json '<json>'", file=sys.stderr)
        return 2
    tool, rest = args[0], args[1:]
    try:
        payload = json.loads(rest[0]) if rest else {}
    except json.JSONDecodeError as exc:
        print(f"invalid json: {exc}", file=sys.stderr)
        return 2

    root = Path(payload.pop("root", PROJECT_DIR))
    handlers = {
        "symbol_search": lambda: code_intel.symbol_search(
            payload.get("query", ""), root, int(payload.get("limit", 30))
        ),
        "get_callers": lambda: code_intel.get_callers(
            payload.get("symbol", ""), root, int(payload.get("limit", 20))
        ),
        "get_callees": lambda: code_intel.get_callees(
            payload.get("symbol", ""), root, int(payload.get("limit", 20))
        ),
        "analyze_impact": lambda: code_intel.analyze_impact(
            payload.get("symbol", ""), root, int(payload.get("max_depth", 4))
        ),
        "find_related_tests": lambda: code_intel.find_related_tests(
            payload.get("symbol", ""), root, int(payload.get("limit", 20))
        ),
        "get_ai_context": lambda: code_intel.symbol_search(
            payload.get("symbol") or Path(str(payload.get("path", ""))).stem, root
        ),
        "symbols_in_file": lambda: code_intel.symbols_in_file(
            payload.get("path", ""), root, int(payload.get("limit", 40))
        ),
    }
    handler = handlers.get(tool)
    if handler is None:
        print(f"unsupported tool: {tool}", file=sys.stderr)
        return 2
    print(handler())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
