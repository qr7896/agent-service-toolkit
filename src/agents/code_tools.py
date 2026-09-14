"""第一批"看代码"的工具 —— AI Coding Agent 的第一个魔改（阶段 5）
这两个工具让 Agent 从"只会查手册"升级成"能看代码仓库"：
  - list_files()：知道项目里有哪些文件
  - read_file()： 读某个文件的一段内容（带行号）
三条设计原则（也是和原版 RAG 最大的不同）：
  1) 工具必须限制在项目目录内 —— Agent 不能读项目外的任何文件（安全边界）；
  2) 返回值必须带"坐标"（相对路径 + 行号），否则模型没法引用、没法定位；
  3) 输出必须有上限（文件数、行数），防止一次把整个仓库塞进上下文。
额外一条工程原则：工具要"优雅失败" —— 越权或文件不存在时返回 "ERROR: ..."
字符串交给模型判断，而不是抛异常把整个图炸掉（这是我们踩过的 500 的教训）。
验收方式：
    D:\\codex\\working\\project20260827\\.venv\\Scripts\\python.exe D:\\codex\\working\\lg_practice\\day3_code_tools_check.py
"""
from __future__ import annotations
from pathlib import Path
from langchain_core.tools import tool
# src/agents/code_tools.py -> parents[0]=agents, [1]=src, [2]=仓库根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# 列文件时跳过的噪音目录：里面全是生成物，模型看了也没用，还会刷屏
SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".ruff_cache",
    "node_modules",
    "chroma_db",
}
def _resolve_inside(path_str: str) -> Path:
    """安全闸门：把"用户给的路径"解析成项目内的绝对路径。
    TODO 1：实现这个函数
      - 用 PROJECT_ROOT / path_str 拼出候选路径，再用 .resolve() 变成绝对路径；
      - 如果结果不在 PROJECT_ROOT 之内（例如 "../../outside.txt" 或 "C:/Windows/win.ini"），
        直接 raise ValueError(f"路径超出项目范围: {path_str}")；
      - 否则返回这个绝对路径。
    提示：判断"是否在项目内"可以用 candidate.is_relative_to(PROJECT_ROOT)。
    注意 ./ 与 ../ 都要先 resolve() 之后再判断，否则等于没防。
    """
    candidate = (PROJECT_ROOT / path_str).resolve()
    if not candidate.is_relative_to(PROJECT_ROOT):
        raise ValueError(f"路径超出项目范围: {path_str}")
    return candidate
@tool
def list_files(pattern: str = "**/*", max_files: int = 100) -> str:
    """列出项目内的文件（相对路径，按字母排序）。
    pattern 例如 "**/*.py"、"src/**/*"、"*.toml"。
    TODO 2：实现这个工具
      - 用 PROJECT_ROOT.glob(pattern) 找出候选路径；
      - 只保留文件（p.is_file()），并跳过 SKIP_DIRS 里的目录
        （提示：判断时可以看 p.relative_to(PROJECT_ROOT).parts 里有没有这些名字）；
      - 转成"相对项目根"的字符串（用 / 作为分隔符，跨平台更稳），排序；
      - 最多返回 max_files 行，每行一个路径；
      - 末尾再补一行汇总，例如："(showing 3 of 57 files)"。
    """
    # 安全闸门：模式里带 ../ 会逃出项目根（glob("../*") 实测可列出项目外目录），
    # 与 read_file 同级的安全洞。先归一化判断，越权就优雅返回 ERROR，不抛异常。
    try:
        _resolve_inside(pattern)
    except ValueError as e:
        return f"ERROR: {e}"
    files: list[str] = []
    for p in PROJECT_ROOT.glob(pattern):
        if not p.is_file():
            continue
        rel = p.relative_to(PROJECT_ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        files.append(rel.as_posix())
    files.sort()
    shown = files[:max_files]
    return "\n".join([*shown, f"(showing {len(shown)} of {len(files)} files)"])
@tool
def read_file(path: str, start_line: int = 1, max_lines: int = 200) -> str:
    """读取项目内某个文件的一段内容，返回带行号的文本。
    path 用相对项目根目录的路径，例如 "src/agents/agents.py"。
    TODO 3：实现这个工具
      - 先调用 _resolve_inside(path) 做安全检查；如果它抛 ValueError，
        就 return f"ERROR: {e}"（优雅失败，不要往上抛）；
      - 文件不存在时 return f"ERROR: 文件不存在: {path}"；
      - 用 file.read_text(encoding="utf-8", errors="replace") 读进来，
        再按 "\n" 切成行列表；
      - 只取第 start_line 行开始的 max_lines 行（注意从 1 开始计数），
        每行输出格式："   12 | 该行内容"（行号右对齐，宽度 5 即可）；
      - 如果文件更长、被截断了，末尾补一行：
        f"(lines {start_line}-{end} of {total})"。
    """
    try:
        resolved = _resolve_inside(path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not resolved.is_file():
        # is_file() 同时挡住目录：否则 read_text 会抛 IsADirectoryError 把图炸掉。
        # 目录单独报错，避免误报成"文件不存在"。
        if resolved.is_dir():
            return f"ERROR: 不是文件（是目录）: {path}"
        return f"ERROR: 文件不存在: {path}"
    text = resolved.read_text(encoding="utf-8", errors="replace")
    # 结尾换行是行终止符，不是"额外一行"：去掉后再切行，
    # 否则每个以 \n 结尾的文件都会虚增一行空行、总数多 1
    if text.endswith("\n"):
        text = text[:-1]
    lines = text.split("\n") if text else []
    total = len(lines)
    start = max(1, start_line)
    max_lines = max(1, max_lines)
    end = min(start + max_lines - 1, total)
    out = [f"{i:5d} | {lines[i - 1]}" for i in range(start, end + 1)]
    if end < total:
        out.append(f"(lines {start}-{end} of {total})")
    return "\n".join(out)
