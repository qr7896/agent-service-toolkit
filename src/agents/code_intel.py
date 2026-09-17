"""本地代码智能：CodeGraph 的可用替身（doc 03 §4 / doc 01 §5）。

设计原则（也是项目长期的技术选型原则）：**基础设施成熟就复用，实验对象才自己做**。
CodeGraph 提供结构化代码事实，本项目的研究对象是"Agent 何时取哪种证据"，所以这里不
重造 tree-sitter / call graph 引擎，而是用 Python 标准库 `ast` 提供**同一组只读证据动作**：

    symbol_search / get_callers / get_callees / analyze_impact / find_related_tests

接口与语义对齐 CodeGraph，接入真正的 CodeGraph（MCP / CLI）时可以直接替换实现，
Planner 与 EGCP 不需要改。当前实现只覆盖 Python 静态可解析的部分：
动态分发、生成代码、跨语言引用都看不到——这是它已知的边界，不是 bug。
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents import codegraph
from agents.code_tools import PROJECT_ROOT
from langchain_core.tools import tool

SKIP_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules", "models", "chroma_db",
    ".codex", ".pytest_cache", "build", "dist",
}
# 注意：不要把 `_eval_sandbox` 排除掉。评测任务的文件就在那里，索引看不见它们，
# 证据门控就会永远判"目标未知"（A/B 的 D 组实测踩过：任务一直做不完）。
MAX_IMPACT_DEPTH = 4


@dataclass
class Symbol:
    name: str
    path: str
    lineno: int
    kind: str  # function / class / method
    qualname: str


@dataclass
class CodeIndex:
    symbols: dict[str, list[Symbol]] = field(default_factory=dict)
    callers: dict[str, set[str]] = field(default_factory=dict)
    callees: dict[str, set[str]] = field(default_factory=dict)
    tests: dict[str, set[str]] = field(default_factory=dict)  # symbol -> test 名称
    files_scanned: int = 0

    def definitions(self, name: str) -> list[Symbol]:
        return self.symbols.get(name, [])


_INDEX_CACHE: dict[str, CodeIndex] = {}

# 记录最近一次实际使用的后端，供轨迹与验收查询"到底是 CodeGraph 还是本地索引"
LAST_BACKEND: dict[str, str] = {"backend": "local-ast"}


def _prefer_codegraph(tool: str, **arguments: Any) -> str | None:
    """优先走 CodeGraph；不可用时返回 None，由调用方回退本地实现。

    回退不是静默的：`LAST_BACKEND` 会记下真实后端与回退原因。
    """
    status = codegraph.probe()
    if not status["available"]:
        LAST_BACKEND.update({"backend": "local-ast", "reason": status.get("reason", "")})
        return None
    try:
        text = codegraph.call(tool, **arguments)
    except codegraph.CodeGraphUnavailable as exc:
        LAST_BACKEND.update({"backend": "local-ast", "reason": f"CodeGraph 调用失败：{exc}"})
        return None
    LAST_BACKEND.update({"backend": status["backend"], "reason": ""})
    return text


def backend() -> dict[str, str]:
    return dict(LAST_BACKEND)


def _iter_py_files(root: Path):
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def _is_test_file(rel: str, name: str) -> bool:
    return Path(rel).name.startswith("test_") or Path(rel).name.endswith("_test.py") or "tests" in rel


def build_index(root: Path | None = None, refresh: bool = False) -> CodeIndex:
    """建立（并缓存）索引。解析失败的文件跳过——不因为一个坏文件让整张索引失效。"""
    base = Path(root or PROJECT_ROOT)
    key = str(base)
    if not refresh and key in _INDEX_CACHE:
        return _INDEX_CACHE[key]

    index = CodeIndex()
    pending_calls: list[tuple[str, str]] = []
    for path in _iter_py_files(base):
        rel = path.relative_to(base).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        index.files_scanned += 1
        is_test = _is_test_file(rel, path.name)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = "class" if isinstance(node, ast.ClassDef) else "function"
                symbol = Symbol(node.name, rel, node.lineno, kind, node.name)
                index.symbols.setdefault(node.name, []).append(symbol)
                # 收集该函数体里直接调用的名字，用于 callers / callees
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        func = child.func
                        callee = (
                            func.id
                            if isinstance(func, ast.Name)
                            else func.attr
                            if isinstance(func, ast.Attribute)
                            else None
                        )
                        if callee:
                            pending_calls.append((node.name, callee))
                if is_test and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            func = child.func
                            callee = (
                                func.id
                                if isinstance(func, ast.Name)
                                else func.attr
                                if isinstance(func, ast.Attribute)
                                else None
                            )
                            if callee:
                                index.tests.setdefault(callee, set()).add(
                                    f"{rel}::{node.name}"
                                )

    for caller, callee in pending_calls:
        index.callers.setdefault(callee, set()).add(caller)
        index.callees.setdefault(caller, set()).add(callee)
    _INDEX_CACHE[key] = index
    return index


def symbol_search(query: str, root: Path | None = None, limit: int = 30) -> str:
    """按名字（不区分大小写的子串）搜索符号，返回 `路径:行号 类型 名字`。"""
    remote = _prefer_codegraph("symbol_search", query=query, limit=limit)
    if remote is not None:
        return remote
    index = build_index(root)
    needle = (query or "").strip().lower()
    if not needle:
        return "ERROR: 查询不能为空"
    hits = [
        symbol
        for name, symbols in index.symbols.items()
        if needle in name.lower()
        for symbol in symbols
    ]
    hits.sort(key=lambda item: (item.path, item.lineno))
    if not hits:
        return f"no matches: {query}"
    lines = [f"{s.path}:{s.lineno} {s.kind} {s.name}" for s in hits[:limit]]
    if len(hits) > limit:
        lines.append(f"... 共 {len(hits)} 个，已截断到 {limit}")
    return "\n".join(lines)


def get_callers(symbol: str, root: Path | None = None, limit: int = 20) -> str:
    remote = _prefer_codegraph("get_callers", symbol=symbol, limit=limit)
    if remote is not None:
        return remote
    index = build_index(root)
    names = sorted(index.callers.get(symbol, set()))
    if not names:
        return f"no callers found for {symbol}（静态分析看不到动态调用）"
    return "\n".join([f"caller {name}" for name in names[:limit]])


def get_callees(symbol: str, root: Path | None = None, limit: int = 20) -> str:
    remote = _prefer_codegraph("get_callees", symbol=symbol, limit=limit)
    if remote is not None:
        return remote
    index = build_index(root)
    names = sorted(index.callees.get(symbol, set()))
    if not names:
        return f"no callees found for {symbol}"
    return "\n".join([f"callee {name}" for name in names[:limit]])


def analyze_impact(symbol: str, root: Path | None = None, max_depth: int = MAX_IMPACT_DEPTH) -> str:
    """按调用关系反向展开受影响范围（BFS，有深度上限）。"""
    remote = _prefer_codegraph("analyze_impact", symbol=symbol, max_depth=max_depth)
    if remote is not None:
        return remote
    index = build_index(root)
    seen: set[str] = set()
    frontier = [symbol]
    depth = 0
    while frontier and depth < max_depth:
        depth += 1
        next_frontier: list[str] = []
        for name in frontier:
            for caller in index.callers.get(name, set()):
                if caller not in seen:
                    seen.add(caller)
                    next_frontier.append(caller)
        frontier = next_frontier

    defs = index.definitions(symbol)
    files = sorted({d.path for d in defs})
    target = defs[0] if defs else None
    level = "none" if target is None else "low" if not seen else "medium" if len(seen) <= 3 else "high"
    lines = [
        f"symbol: {symbol}",
        f"defined at: {target.path}:{target.lineno}" if target else "defined at: （未在索引中找到）",
        f"affected callers ({len(seen)}): {', '.join(sorted(seen)) or '（无）'}",
        f"affected files: {', '.join(files) or '（无）'}",
        f"impact_level: {level}",
    ]
    return "\n".join(lines)


def find_related_tests(symbol: str, root: Path | None = None, limit: int = 20) -> str:
    """找直接调用该符号、或调用其 caller 的测试。"""
    remote = _prefer_codegraph("find_related_tests", symbol=symbol, limit=limit)
    if remote is not None:
        return remote
    index = build_index(root)
    related = set(index.tests.get(symbol, set()))
    for caller in index.callers.get(symbol, set()):
        related |= index.tests.get(caller, set())
    if not related:
        return f"no related tests found for {symbol}"
    return "\n".join(sorted(related)[:limit])


def symbols_in_file(path: str, root: Path | None = None, limit: int = 40) -> str:
    """列出某个文件里定义的符号，输出格式与 symbol_search 一致（`路径:行号 类型 名字`）。

    这是"已知要改哪个文件、但还不知道具体改哪个符号"时的取证动作：
    没有它，证据门控的 target 维度补不满，门就从"门"变成"墙"。
    """
    index = build_index(root)
    target = str(path or "").replace("\\", "/")
    hits = sorted(
        (symbol for symbols in index.symbols.values() for symbol in symbols if symbol.path == target),
        key=lambda item: item.lineno,
    )
    if not hits:
        return f"no symbols found in {path}"
    return "\n".join(f"{s.path}:{s.lineno} {s.kind} {s.name}" for s in hits[:limit])


def index_summary(root: Path | None = None) -> dict[str, Any]:
    index = build_index(root)
    return {
        "files_scanned": index.files_scanned,
        "symbols": len(index.symbols),
        "call_edges": sum(len(v) for v in index.callers.values()),
        "tested_symbols": len(index.tests),
    }


# ---- 给 Agent 用的工具封装 -------------------------------------------------
# 与 search_code / read_file 并列，由配置决定是否绑定（A/B 实验里"用了代码智能"这一组）


@tool("symbol_search")
def symbol_search_tool(query: str) -> str:
    """按符号名（函数 / 类，不区分大小写）搜索，返回 路径:行号 与类型。
    比全文搜索更准：它只认代码里真实定义过的符号。"""
    return symbol_search(query)


@tool("get_callers")
def get_callers_tool(symbol: str) -> str:
    """查某个符号被谁调用（反向依赖）。改之前用它确认影响面。"""
    return get_callers(symbol)


@tool("analyze_impact")
def analyze_impact_tool(symbol: str) -> str:
    """按调用关系反向展开影响范围，返回受影响的调用者与文件、影响等级。"""
    return analyze_impact(symbol)


@tool("find_related_tests")
def find_related_tests_tool(symbol: str) -> str:
    """找与某个符号相关的测试用例，用于确定"改完怎么证明它对"。"""
    return find_related_tests(symbol)


CODE_INTEL_TOOLS = [
    symbol_search_tool,
    get_callers_tool,
    analyze_impact_tool,
    find_related_tests_tool,
]


__all__ = [
    "CodeIndex",
    "CODE_INTEL_TOOLS",
    "Symbol",
    "backend",
    "analyze_impact",
    "build_index",
    "find_related_tests",
    "get_callees",
    "get_callers",
    "index_summary",
    "symbol_search",
    "symbol_search_tool",
    "symbols_in_file",
]
