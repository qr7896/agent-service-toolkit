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

import json
import os
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SANDBOX_ROOT = PROJECT_ROOT / ".codex" / "sandboxes"

# 复制时排除：版本库、虚拟环境、本地数据与各类缓存。副本只需要"能跑起来"。
EXCLUDED_DIRS = {
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
# `.git` 刻意**不排除**（只有 3.5MB）：副本因此是真正的仓库，
# 沙箱内 Agent 的 git_diff 工具才有东西可查，任务结束也能直接 `git diff` 出 patch。
# 第一版把它排除了，结果沙箱里 git_diff 是坏的、也没法产出补丁。

DEFAULT_MAX_AGE_HOURS = 6


def _remove_tree(path: Path) -> bool:
    """删目录并**如实返回结果**。

    `.git` 里的对象文件是只读的，Windows 上直接 `rmtree` 会失败——第一版用
    `ignore_errors=True` 还返回 True，于是"回收成功"是假的，副本会一直堆着。
    这里先把只读位清掉再删，并且删完检查目录是否真的消失。
    """
    if not path.exists():
        return True

    def _force(func, target, _exc):
        try:
            os.chmod(target, 0o700)
            func(target)
        except OSError:
            pass

    try:
        shutil.rmtree(path, onexc=_force)
    except TypeError:  # 老版本 Python 只有 onerror
        shutil.rmtree(path, onerror=_force)
    except OSError:
        pass
    return not path.exists()


def _ignore(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in EXCLUDED_DIRS}


def sandbox_path(name: str, pid: int | None = None, stamp: str | None = None) -> Path:
    """沙箱目录名带 pid + 时间戳：进程被强杀后，启动时能凭这两样判断副本是不是孤儿。"""
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)
    if not safe:
        raise ValueError("sandbox name must contain at least one usable character")
    if pid is None and stamp is None:
        return SANDBOX_ROOT / safe  # 兼容旧调用（仅用于推导路径，不用于创建）
    resolved_pid = os.getpid() if pid is None else pid
    resolved_stamp = stamp or datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return SANDBOX_ROOT / f"{safe}-{resolved_pid}-{resolved_stamp}"


def create_sandbox(name: str, source: Path | None = None) -> Path:
    """把工作区复制成一份独立副本；创建前先做一次 GC（"启动时兜底"那一侧）。

    回收必须是"任务结束时 + 启动时"两侧都有：`finally` 只能覆盖正常路径，
    `kill -9` / OOM / 断电留下的副本只能靠下一次启动来清。
    """
    gc_sandboxes()  # 启动时兜底：清掉上次异常退出留下的孤儿副本
    target = sandbox_path(name)
    if target.exists():  # 兼容：手工建过的同名目录
        _remove_tree(target)
    target = sandbox_path(name, pid=os.getpid())
    if target.exists():
        _remove_tree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source or PROJECT_ROOT, target, ignore=_ignore, symlinks=False)
    (target / "sandbox.json").write_text(
        json.dumps(
            {
                "name": name,
                "pid": os.getpid(),
                "created_at": datetime.now(UTC).isoformat(),
                "source": str(source or PROJECT_ROOT),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    _commit_baseline(target)
    return target


def _commit_baseline(sandbox: Path) -> None:
    """在副本里把当前状态固化成一次 baseline 提交。

    这样 `git diff` 得到的**只有任务期间的改动**，不会把原仓库里本来就有的未提交改动
    混进补丁。用 `-c user.*` 显式给身份，不依赖机器上的 git 配置。
    """
    git = [
        "git",
        "-C",
        str(sandbox),
        "-c",
        "user.name=codex-sandbox",
        "-c",
        "user.email=sandbox@local",
    ]
    try:
        subprocess.run([*git, "add", "-A"], capture_output=True, timeout=120)
        subprocess.run(
            [*git, "commit", "-q", "-m", "sandbox baseline"], capture_output=True, timeout=120
        )
    except (OSError, subprocess.SubprocessError):
        pass  # 没有 git 或提交失败都不阻塞任务，patch 退化为对比 HEAD


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        # Windows 上不能用 os.kill(pid, 0)：那会真的去终止进程
        try:
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError):
            return True  # 查不了就保守地当成活着，避免误删
        return str(pid) in out.stdout
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def gc_sandboxes(
    max_age_hours: float = DEFAULT_MAX_AGE_HOURS, now: float | None = None
) -> dict[str, list[str]]:
    """回收孤儿副本：记录里的进程已经死了就删；没有记录的老目录按 mtime 删。

    进程还活着的副本一律保留——它可能是另一个正在跑的任务。
    """
    report: dict[str, list[str]] = {"removed": [], "kept": [], "orphan_pid": [], "stale": []}
    if not SANDBOX_ROOT.exists():
        return report
    current = now or time.time()
    for child in SANDBOX_ROOT.iterdir():
        if not child.is_dir():
            continue
        meta_path = child / "sandbox.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                meta = {}
            pid = int(meta.get("pid") or 0)
            if pid and _pid_alive(pid):
                report["kept"].append(child.name)
                continue
            if _remove_tree(child):
                report["removed"].append(child.name)
                report["orphan_pid"].append(child.name)
            else:
                report["kept"].append(child.name)
            continue
        age_hours = (current - child.stat().st_mtime) / 3600
        if age_hours > max_age_hours:
            if _remove_tree(child):
                report["removed"].append(child.name)
                report["stale"].append(child.name)
            else:
                report["kept"].append(child.name)
        else:
            report["kept"].append(child.name)
    return report


def export_patch(sandbox: Path) -> dict[str, Any]:
    """把副本里的改动导出成 patch —— Sandbox 的产物是补丁，不是"一个改好的仓库"。"""
    git = ["git", "-C", str(sandbox)]
    subprocess.run([*git, "add", "-A", "-N"], capture_output=True, timeout=120)
    diff = subprocess.run(
        [*git, "diff"], capture_output=True, encoding="utf-8", errors="replace", timeout=120
    )
    names = subprocess.run(
        [*git, "diff", "--name-only"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    return {
        "patch": diff.stdout or "",
        "changed_files": [
            line.strip() for line in (names.stdout or "").splitlines() if line.strip()
        ],
    }


def collect_result(sandbox: Path, test_result: dict[str, Any] | None = None) -> dict[str, Any]:
    """Sandbox 的标准产出：patch + 验证结果。原始仓库全程没有被写过。"""
    result = export_patch(sandbox)
    result["test_result"] = test_result or {}
    result["sandbox"] = str(sandbox)
    result["apply_hint"] = "git apply <patch 文件>（确认无误后再 apply 到原始仓库）"
    return result


def reclaim_sandbox(path: Path) -> bool:
    """回收副本。只允许删沙箱根目录下的东西，避免手滑指向真实工作区。"""
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(SANDBOX_ROOT.resolve()) or resolved == SANDBOX_ROOT.resolve():
        raise ValueError(f"refusing to reclaim non-sandbox path: {resolved}")
    if not resolved.exists():
        return False
    return _remove_tree(resolved)


def sandbox_env(path: Path) -> dict[str, str]:
    """在副本里运行需要的环境变量：源码路径指向副本，而不是主工作区。"""
    import os

    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(path) / "src")
    return env


__all__ = [
    "DEFAULT_MAX_AGE_HOURS",
    "EXCLUDED_DIRS",
    "PROJECT_ROOT",
    "SANDBOX_ROOT",
    "collect_result",
    "create_sandbox",
    "export_patch",
    "gc_sandboxes",
    "reclaim_sandbox",
    "sandbox_env",
    "sandbox_path",
]
