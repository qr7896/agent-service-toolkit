"""测试执行工具：让 Agent 能真正"运行并观察结果"。

对应 v3 总纲——LLM 负责提出方案，确定性系统负责验证事实。测试结果就是这套系统里
最硬的 ground truth 之一：它不由模型自证，而是由 pytest 给出。

安全边界（v3 §35 的"改错了怎么办 / 谁负责验证"）：
  1) 只跑 pytest：argv 自己拼装，绝不 shell=True，不接受任意命令；
  2) path 必须落在项目根内（复用 code_tools 的 _resolve_inside 闸门）；
  3) path 以 "-" 开头一律拒绝，避免被当成 pytest 选项注入；
  4) 输出行数与执行时长都有上限，超时直接放弃而不是把图卡死。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from langchain_core.tools import tool

from agents.code_tools import PROJECT_ROOT, _resolve_inside

MIN_TIMEOUT = 5
MAX_TIMEOUT = 600
DEFAULT_MAX_LINES = 200


def _cap(text: str, max_lines: int) -> tuple[list[str], bool]:
    """按行截断文本，返回 (保留的行, 是否被截断)。"""
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return lines, False
    return lines[:max_lines], True


@tool
def run_tests(
    path: str = "",
    timeout: int = 120,
    max_lines: int = DEFAULT_MAX_LINES,
) -> str:
    """运行项目测试（只允许 pytest），返回结构化结果。

    参数：
      - path：可选，测试文件或目录（相对项目根，例如 "tests/schema"）；留空则跑全部
      - timeout：秒；超过就放弃并返回 status: timeout（默认 120，自动夹在 5–600 之间）
      - max_lines：输出最多保留多少行，超出会截断并标记

    输出契约（字段固定，便于下游节点与模型共同解析）：

        command: <实际执行的命令>
        exit_code: <0/1/5/...>
        status: passed | failed | no_tests | timeout | error
        passed: true | false | na
        summary: <pytest 的最后一行，例如 "10 passed in 6.75s">
        output:
        <stdout + stderr，最多 max_lines 行>

    约定：
      - exit_code 0 → status: passed / passed: true
      - exit_code 5 → status: no_tests / passed: na（没有可跑的测试，不算失败）
      - exit_code 2/3/4 → status: error（pytest 自己出错：用法/中断/内部错误）
      - 其他非 0 → status: failed / passed: false
      - 失败时 output 里必须保留 traceback（含测试文件名与行号），否则 Debug 无从下手
      - 越权路径、非法参数、pytest 不可用 → 以 "ERROR: " 开头的字符串
    """
    try:
        # --- 参数校验 -------------------------------------------------
        try:
            timeout_s = int(timeout)
        except (TypeError, ValueError):
            return f"ERROR: timeout 必须是整数秒: {timeout!r}"
        timeout_s = max(MIN_TIMEOUT, min(MAX_TIMEOUT, timeout_s))

        try:
            max_lines_n = int(max_lines)
        except (TypeError, ValueError):
            return f"ERROR: max_lines 必须是整数: {max_lines!r}"
        max_lines_n = max(10, max_lines_n)

        target_arg = ""
        if path:
            if path.strip().startswith("-"):
                return f"ERROR: 非法参数（不允许以 - 开头的选项）: {path}"
            try:
                resolved = _resolve_inside(path)
            except ValueError as e:
                return f"ERROR: {e}"
            if not resolved.exists():
                return f"ERROR: 测试路径不存在: {path}"
            target_arg = resolved.relative_to(PROJECT_ROOT).as_posix()

        # --- 组装命令（白名单：只有 pytest，且不经 shell） --------------
        argv = [sys.executable, "-m", "pytest", "-q"]
        if target_arg:
            argv.append(target_arg)
        command = " ".join(["python", "-m", "pytest", "-q", *([target_arg] if target_arg else [])])

        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

        timed_out = False
        try:
            proc = subprocess.run(
                argv,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_s,
                env=env,
            )
            exit_code = proc.returncode
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
        except subprocess.TimeoutExpired as e:
            timed_out = True
            exit_code = -1
            stdout = e.stdout or ""
            stderr = e.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
        except FileNotFoundError:
            return "ERROR: 找不到 python 解释器，无法运行 pytest"

        # --- 归一化输出与状态 ------------------------------------------
        combined = (stdout + ("\n" + stderr if stderr.strip() else "")).strip()
        if "No module named pytest" in combined:
            return "ERROR: 当前 Python 环境没有安装 pytest"

        if timed_out:
            status, passed = "timeout", "na"
            summary = f"timeout after {timeout_s}s"
        elif exit_code == 0:
            status, passed = "passed", "true"
            summary = combined.splitlines()[-1].strip() if combined else "no output"
        elif exit_code == 5:
            status, passed = "no_tests", "na"
            summary = "no tests ran"
        elif exit_code in (2, 3, 4):
            status, passed = "error", "false"
            summary = combined.splitlines()[-1].strip() if combined else f"pytest exit {exit_code}"
        else:
            status, passed = "failed", "false"
            summary = combined.splitlines()[-1].strip() if combined else f"pytest exit {exit_code}"

        kept, truncated = _cap(combined, max_lines_n)
        out = [
            f"command: {command}",
            f"exit_code: {exit_code}",
            f"status: {status}",
            f"passed: {passed}",
            f"summary: {summary}",
            "output:",
            *kept,
        ]
        if truncated:
            out.append(f"(output truncated at {max_lines_n} lines; {len(combined.splitlines())} lines total)")
        return "\n".join(out)
    except Exception as e:  # 任何异常都不抛出图外
        return f"ERROR: {e}"
