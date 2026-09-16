"""任务级工作区隔离（阶段 19）。

为什么不能只靠"路径必须落在项目内"：那条约束保证的是 Agent 不跑到仓库外面去，
但它默认**要改的就是开发者的真实工作区**——模型一旦判断失误，被改坏的是你正在
开发的仓库。这里把执行环境整体复制一份，任务在副本里跑，跑完连副本一起丢掉。

实现上刻意选了"整树复制 + 以副本为工作目录运行"，而不是把 `PROJECT_ROOT` 改成
可注入的函数：后者要动 20 处引用、还要保证 15 个已通过的验收不变；而整树复制不需要
改任何现有代码——`PROJECT_ROOT` 是从 `__file__` 推出来的，副本里的解析结果自然就是副本。

这是路线图 §19 说的"先做路径限制 + git diff，再考虑 Docker / WSL2 / Worktree"里的
中间那一步：真隔离、可整体回收，但还不涉及容器。
"""

from __future__ import annotations

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SANDBOX_ROOT = PROJECT_ROOT / ".codex" / "sandboxes"

# 复制时排除：版本库、虚拟环境、本地数据与各类缓存。副本只需要"能跑起来"。
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    ".codex",
    "models",
    "node_modules",
    "chroma_db",
    "__pycache__",
    ".pytest_cache",
    "_eval_sandbox",
    ".mypy_cache",
    ".ruff_cache",
}


def _ignore(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in EXCLUDED_DIRS}


def sandbox_path(name: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)
    if not safe:
        raise ValueError("sandbox name must contain at least one usable character")
    return SANDBOX_ROOT / safe


def create_sandbox(name: str, source: Path | None = None) -> Path:
    """把工作区复制成一份独立副本；同名副本会被先清掉，保证每次都是干净起点。"""
    target = sandbox_path(name)
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source or PROJECT_ROOT, target, ignore=_ignore, symlinks=False)
    return target


def reclaim_sandbox(path: Path) -> bool:
    """回收副本。只允许删沙箱根目录下的东西，避免手滑指向真实工作区。"""
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(SANDBOX_ROOT.resolve()) or resolved == SANDBOX_ROOT.resolve():
        raise ValueError(f"refusing to reclaim non-sandbox path: {resolved}")
    if not resolved.exists():
        return False
    shutil.rmtree(resolved, ignore_errors=True)
    return True


def sandbox_env(path: Path) -> dict[str, str]:
    """在副本里运行需要的环境变量：源码路径指向副本，而不是主工作区。"""
    import os

    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(path) / "src")
    return env


__all__ = [
    "EXCLUDED_DIRS",
    "PROJECT_ROOT",
    "SANDBOX_ROOT",
    "create_sandbox",
    "reclaim_sandbox",
    "sandbox_env",
    "sandbox_path",
]
