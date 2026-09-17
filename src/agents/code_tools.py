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

import re
import subprocess
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
# 搜索时单文件大小上限：超过就跳过，避免扫巨型文件
MAX_SEARCH_FILE_SIZE = 1_000_000  # 1 MB


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


@tool
def search_code(
    query: str,
    path_glob: str = "**/*.py",
    max_matches: int = 50,
    # 默认放宽到 200：本仓库有 80+ 个 .py 文件，50 会让每次搜索都被标成 truncated，
    # 这个标记就失去意义了（truncated 应该表示"确实没扫完"）。
    max_files: int = 200,
    context_lines: int = 0,
    case_sensitive: bool = False,
    regex: bool = False,
) -> str:
    """在项目代码里搜索关键词 / 函数名 / 类名，返回"相对路径:行号 + 命中行"。
    这是让 Agent "先定位、再精读"的关键工具：先用它找到可疑位置，再用 read_file
    读那几行上下文，而不是把整个仓库挨个读完。
    TODO：实现这个工具。输出格式必须严格遵守下面的契约（验收脚本按格式判定）：
      - 第一行是汇总行：
            有命中且未截断 -> f"matches: {n} in {m} files"
            命中被截断     -> f"matches: {n}+ (truncated) in {m} files"
            完全没有命中   -> f"no matches for {query!r} in {path_glob}"
      - 之后每个命中/上下文一行：
            命中行    -> f"{rel_path}:{line_no}: {line_text}"
            上下文行  -> f"{rel_path}:{line_no}| {line_text}"
      - 顺序：先按文件路径字母序，再按行号升序。
      - 同一文件里相邻命中共享的上下文不要重复输出。
    必须满足的约束（对应路线图 §11 的工具设计原则）：
      1) 路径不能越权：先用 _resolve_inside(path_glob) 校验，
         越权时 return f"ERROR: {e}"，不要抛异常；
      2) 跳过 SKIP_DIRS 里的目录；
      3) 读不了的文件 / 像二进制的文件（例如含 NUL 字节）直接跳过，不要崩；
      4) 单个文件要有大小上限（例如超过 1 MB 跳过），避免扫巨型文件；
      5) query 默认按普通文本匹配（正则元字符要用 re.escape 转义）；
         regex=True 时按正则匹配，正则非法时
         return f"ERROR: 无效的正则表达式: {e}"；
      6) case_sensitive=False 时忽略大小写；
      7) 达到 max_matches 或 max_files 立即停止扫描，并在汇总行标记 truncated；
      8) 其他任何异常都不要抛出图外，返回以 "ERROR:" 开头的字符串。
    """
    try:
        # 1) 安全闸门：模式里带 ../ 会逃出项目根，与 list_files 同级的安全洞。
        try:
            _resolve_inside(path_glob)
        except ValueError as e:
            return f"ERROR: {e}"

        # 5) 编译模式：默认普通文本（re.escape 转义），regex=True 走正则。
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(query, flags) if regex else re.compile(re.escape(query), flags)
        except re.error as e:
            return f"ERROR: 无效的正则表达式: {e}"

        # 2) 收集候选文件：只留文件、跳过 SKIP_DIRS，按相对路径字母序。
        candidates: list[Path] = []
        for p in PROJECT_ROOT.glob(path_glob):
            if not p.is_file():
                continue
            rel = p.relative_to(PROJECT_ROOT)
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            candidates.append(p)
        candidates.sort(key=lambda p: p.relative_to(PROJECT_ROOT).as_posix())

        total_matches = 0  # 已命中的总行数（含因截断停止前的所有命中）
        matched_files = 0  # 有命中的文件数
        files_scanned = 0  # 实际扫描过的文件数（跳过的不算）
        truncated = False
        out: list[str] = []

        for p in candidates:
            # 7) 达到 max_files 立即停止，标记 truncated
            if files_scanned >= max_files:
                truncated = True
                break
            # 3)/4) 读不了的文件、像二进制的文件（NUL 字节）、超过大小上限的文件直接跳过
            try:
                if p.stat().st_size > MAX_SEARCH_FILE_SIZE:
                    continue
                data = p.read_bytes()
                if b"\x00" in data:
                    continue
                text = data.decode("utf-8", errors="replace")
            except Exception:
                continue
            files_scanned += 1
            rel = p.relative_to(PROJECT_ROOT).as_posix()
            # 与 read_file 保持同一行号口径：结尾换行是行终止符，不是"额外一行"，
            # 否则每个以 \n 结尾的文件都会虚增一行空行、坐标对不上
            if text.endswith("\n"):
                text = text[:-1]
            lines = text.split("\n") if text else []

            hit_lines: list[int] = []
            for lineno, line in enumerate(lines, 1):
                if pattern.search(line):
                    hit_lines.append(lineno)
                    total_matches += 1
                    # 7) 达到 max_matches 立即停止扫描，标记 truncated
                    if total_matches >= max_matches:
                        truncated = True
                        break

            if hit_lines:
                matched_files += 1
                # 4) 上下文去重：把每个命中的 [hit-c, hit+c] 区间并起来，只输出一次
                ctx: set[int] = set()
                for h in hit_lines:
                    lo = max(1, h - context_lines)
                    hi = min(len(lines), h + context_lines)
                    ctx.update(range(lo, hi + 1))
                hit_set = set(hit_lines)
                for ln in sorted(ctx):
                    if ln in hit_set:
                        out.append(f"{rel}:{ln}: {lines[ln - 1]}")
                    else:
                        out.append(f"{rel}:{ln}| {lines[ln - 1]}")

            if truncated:
                break

        # 汇总行：完全没命中 / 命中 / 命中被截断
        # 注意：一条都没搜到时必须返回 no matches（哪怕扫描过程被截断），
        # 否则模型会把 "0+ (truncated)" 误读成"可能还有命中"。
        if total_matches == 0:
            return f"no matches for {query!r} in {path_glob}"
        if truncated:
            summary = f"matches: {total_matches}+ (truncated) in {matched_files} files"
        else:
            summary = f"matches: {total_matches} in {matched_files} files"
        return "\n".join([summary, *out])
    except Exception as e:  # 8) 任何其他异常都不抛出图外
        return f"ERROR: {e}"


# 敏感文件黑名单：这些文件不允许被 Agent 写入/修改（对应 v3 的 Permission Boundary）
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12"}


def _count_lines(text: str) -> int:
    """数行数，口径与 read_file 保持一致：末尾换行是行终止符，不算额外一行。"""
    if not text:
        return 0
    if text.endswith("\n"):
        text = text[:-1]
    return len(text.split("\n")) if text else 0


def _is_sensitive(rel_path: Path) -> bool:
    """判断相对路径是否属于"禁止写入"的敏感文件。

    命中任意一条即算敏感（write_file / edit_file 共用这道闸门）：
      - 文件名以 ".env" 开头（.env、.env.local…）
      - 后缀在 SENSITIVE_SUFFIXES 里（.pem / .key / .p12）
      - 文件名以 "id_rsa" 开头
      - 路径里任何一段是 ".git"
    """
    name = rel_path.name.lower()
    if name.startswith(".env"):
        return True
    if rel_path.suffix.lower() in SENSITIVE_SUFFIXES:
        return True
    if name.startswith("id_rsa"):
        return True
    return ".git" in rel_path.parts


@tool
def write_file(path: str, content: str, overwrite: bool = False) -> str:
    """**新建**文件（默认不允许覆盖已有文件）。

    这是"写"能力的第一道闸门：它只负责创建新文件；要改已有文件请用 edit_file，
    因为局部 patch 比整文件重写安全得多（改动小、diff 清晰、容易被 review 和回滚）。

    输出契约：
      - 成功新建           -> "OK: created {rel_path} ({n} lines)"
      - 覆盖已有文件       -> "OK: overwrote {rel_path} ({old_n} -> {n} lines)"
      - 路径越权           -> "ERROR: 路径超出项目范围: ..."
      - 敏感文件           -> "ERROR: 禁止写入敏感文件: {path}"
      - 目标是目录         -> "ERROR: 目标是目录: {path}"
      - 已存在但未授权覆盖 -> "ERROR: 文件已存在，请用 edit_file 局部修改，或显式 overwrite=True: {path}"
    """
    try:
        try:
            target = _resolve_inside(path)
        except ValueError as e:
            return f"ERROR: {e}"

        rel = target.relative_to(PROJECT_ROOT).as_posix()
        if _is_sensitive(Path(rel)):
            return f"ERROR: 禁止写入敏感文件: {path}"

        if target.exists():
            if target.is_dir():
                return f"ERROR: 目标是目录: {path}"
            if not overwrite:
                return f"ERROR: 文件已存在，请用 edit_file 局部修改，或显式 overwrite=True: {path}"
            old_n = _count_lines(target.read_text(encoding="utf-8", errors="replace"))
            target.write_text(content, encoding="utf-8")
            return f"OK: overwrote {rel} ({old_n} -> {_count_lines(content)} lines)"

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"OK: created {rel} ({_count_lines(content)} lines)"
    except Exception as e:
        return f"ERROR: {e}"


@tool
def edit_file(path: str, old_text: str, new_text: str) -> str:
    """**局部修改**已有文件：把唯一命中的 old_text 替换为 new_text。

    为什么不做整文件重写：局部 patch 的改动范围小、diff 清晰、容易验证与回滚。
    为了安全，old_text 必须在文件里**恰好出现一次**——0 处说明片段写错了，
    多处说明片段不够独特，两种情况都必须让模型重新收敛，而不是猜一个位置改。

    输出契约：
      - 成功                -> "OK: edited {rel_path}:{line_no} ({old_lines} -> {new_lines} lines)"
      - 路径越权            -> "ERROR: 路径超出项目范围: ..."
      - 敏感文件            -> "ERROR: 禁止修改敏感文件: {path}"
      - 文件不存在          -> "ERROR: 文件不存在: {path}"
      - old_text 为空       -> "ERROR: old_text 不能为空: {path}"
      - old_text 命中 0 处  -> "ERROR: 未找到 old_text（0 处命中）: {path}"
      - old_text 命中多处   -> "ERROR: old_text 命中 {n} 处，请提供更精确的片段: {path}"
    """
    try:
        try:
            target = _resolve_inside(path)
        except ValueError as e:
            return f"ERROR: {e}"

        rel = target.relative_to(PROJECT_ROOT).as_posix()
        if _is_sensitive(Path(rel)):
            return f"ERROR: 禁止修改敏感文件: {path}"
        if not target.is_file():
            return f"ERROR: 文件不存在: {path}"
        if not old_text:
            return f"ERROR: old_text 不能为空: {path}"

        text = target.read_text(encoding="utf-8", errors="replace")
        hits = text.count(old_text)
        if hits == 0:
            return f"ERROR: 未找到 old_text（0 处命中）: {path}"
        if hits > 1:
            return f"ERROR: old_text 命中 {hits} 处，请提供更精确的片段: {path}"

        # 替换发生处的行号（1 起算）
        line_no = text[: text.index(old_text)].count("\n") + 1
        target.write_text(text.replace(old_text, new_text, 1), encoding="utf-8")
        return (
            f"OK: edited {rel}:{line_no} "
            f"({_count_lines(old_text)} -> {_count_lines(new_text)} lines)"
        )
    except Exception as e:
        return f"ERROR: {e}"


def _git(args: list[str], timeout: int = 30) -> tuple[int, str, str]:
    """在项目根目录执行 git 命令，返回 (exit_code, stdout, stderr)。

    找不到 git 可执行文件时抛 FileNotFoundError，由调用方转成 ERROR 字符串。
    """
    proc = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


@tool
def git_diff(path: str = "", staged: bool = False, max_lines: int = 400) -> str:
    """查看改动（等价于 git diff）：改了哪些文件、具体改了什么。

    这是"改动可见"的机制——改完代码必须能说清改了什么，否则测试、调试、复审和
    人工核查都无从下手。注意 git diff 只看已跟踪文件，所以这里额外给出 status 段，
    让新建的未跟踪文件也能被看见。

    参数：
      - path：可选，只看这个路径（文件或目录），相对项目根，例如 "src/agents/code_tools.py"
      - staged：为 True 时看暂存区改动（git diff --cached）
      - max_lines：diff 正文最多输出多少行，超出会截断

    输出契约：
      - 干净            -> "no changes"（限定 path 时为 "no changes for {rel}"）
      - 有改动          -> 首行 "changes: {n} entries, +{added}/-{removed}"，超长时加 " (truncated)"
                           之后可选 "status:" 段（最多 20 行 git status --short）
                           之后可选 "diff:" 段（git diff 正文，最多 max_lines 行）
                           截断时末尾追加 "(diff truncated at {max_lines} lines; {total} lines total)"
      - 路径越权        -> "ERROR: 路径超出项目范围: ..."
      - 没装 git        -> "ERROR: 未找到 git 命令"
      - 不是 git 仓库   -> "ERROR: 不是 git 仓库 ..."
      - 其他异常        -> "ERROR: {e}"
    """
    try:
        if path:
            try:
                target = _resolve_inside(path)
            except ValueError as e:
                return f"ERROR: {e}"
            rel = target.relative_to(PROJECT_ROOT).as_posix()
            pathspec = ["--", rel]
        else:
            rel = ""
            pathspec = []

        try:
            code, _, err = _git(["rev-parse", "--is-inside-work-tree"])
        except FileNotFoundError:
            return "ERROR: 未找到 git 命令"
        except subprocess.TimeoutExpired:
            return "ERROR: git 命令超时"
        if code != 0:
            reason = " ".join(err.split())[:120] or "git rev-parse 失败"
            return f"ERROR: 不是 git 仓库或 git 不可用: {reason}"

        diff_flags = ["--no-color"] + (["--cached"] if staged else [])
        _, diff_text, _ = _git(["diff", *diff_flags, *pathspec])
        _, status_text, _ = _git(["status", "--short", "--untracked-files=all", *pathspec])
        _, numstat_text, _ = _git(["diff", "--numstat", *diff_flags, *pathspec])

        status_lines = [ln for ln in status_text.splitlines() if ln.strip()]
        diff_lines = diff_text.splitlines()

        # staged=True 时只看暂存区：git status --short 的两位状态码里，
        # 第一位（index 状态）是空格或 "?" 表示"没进暂存区"，这类条目要过滤掉，
        # 否则模型会把"工作区改动"误读成"已暂存改动"。
        if staged:
            status_lines = [ln for ln in status_lines if len(ln) > 2 and ln[0] not in " ?"]

        added = removed = 0
        for ln in numstat_text.splitlines():
            parts = ln.split("\t")
            if len(parts) >= 2:
                added += int(parts[0]) if parts[0].isdigit() else 0
                removed += int(parts[1]) if parts[1].isdigit() else 0

        if not status_lines and not diff_lines:
            return f"no changes for {rel}" if rel else "no changes"

        truncated = len(diff_lines) > max_lines
        summary = f"changes: {len(status_lines)} entries, +{added}/-{removed}"
        if truncated:
            summary += " (truncated)"

        out = [summary]
        if status_lines:
            out.append("status:")
            out.extend(status_lines[:20])
            if len(status_lines) > 20:
                out.append(f"(status truncated: showing 20 of {len(status_lines)} entries)")
        if diff_lines:
            out.append("diff:")
            out.extend(diff_lines[:max_lines])
            if truncated:
                out.append(f"(diff truncated at {max_lines} lines; {len(diff_lines)} lines total)")
        return "\n".join(out)
    except subprocess.TimeoutExpired:
        return "ERROR: git 命令超时"
    except Exception as e:
        return f"ERROR: {e}"
