"""冲突分类与分流（静态优先，实验兜底）。

两类冲突的分界是机械的，不该靠感觉：

  **静态可判** —— 符号不存在、路径越界、目标文件不存在、经验引用的文件已经变了。
  程序直接判，不跑实验，出口是 `evidence_insufficient` 或 `stale_experience`。

  **必须靠实验** —— 两种做法都能通过静态检查，但行为不同。只有这类才轮到沙箱 A/B。

规则本身也是确定性的：**先过静态检查，静态判不了才升级到实验**。这样成本才有界——
绝大多数冲突在符号层就解决了，昂贵的沙箱 A/B 只留给少数真需要跑的。

第一版只做"分类 + 预算闸门"，不自动跑实验：`needs_experiment` 只是**请求**，
真正的 A/B 由调用方在预算内决定是否执行（默认最多 1 组）。
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from agents import code_intel
from agents.code_tools import PROJECT_ROOT

EXIT_OK = "ok"
EXIT_STALE = "stale_experience"
EXIT_INSUFFICIENT = "evidence_insufficient"
EXIT_EXPERIMENT = "needs_experiment"

# 哪些出口是"程序直接判、不跑实验"
STATIC_EXITS = (EXIT_STALE, EXIT_INSUFFICIENT)


@dataclass
class Conflict:
    kind: str  # out_of_workspace / target_missing / symbol_missing / stale_experience / behaviour_ambiguous
    static: bool
    detail: str
    exit: str = ""


@dataclass
class ConflictVerdict:
    exit: str = EXIT_OK
    static_conflicts: list[dict[str, Any]] = field(default_factory=list)
    experiment: dict[str, Any] = field(default_factory=lambda: {"required": False, "reason": ""})
    experiments_allowed: int = 1
    experiments_requested: int = 0

    @property
    def static_only(self) -> bool:
        return not self.experiment.get("required", False)


def _resolve_inside(path_str: str, root: Path) -> Path | None:
    """路径必须落在工作区内——这条是纯静态判断，不需要跑任何东西。"""
    try:
        candidate = (root / path_str).resolve()
    except (OSError, ValueError):
        return None
    return candidate if candidate.is_relative_to(root.resolve()) else None


def _content_changed_since(path: str, rev: str, base: Path) -> bool:
    """文件内容相对某个提交是否变了——纯静态判断（`git show` + 比对哈希）。"""
    if not rev:
        return False
    current = base / path
    if not current.exists():
        return True
    try:
        proc = subprocess.run(
            ["git", "-C", str(base), "show", f"{rev}:{path}"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    if proc.returncode != 0:
        return True  # 那个提交里没有这个文件
    old = hashlib.sha256((proc.stdout or "").encode("utf-8", "replace")).hexdigest()
    new = hashlib.sha256(
        current.read_text(encoding="utf-8", errors="replace").encode("utf-8")
    ).hexdigest()
    return old != new


def detect_static_conflicts(
    plan: dict[str, Any],
    root: Path | None = None,
    experiences: list[dict[str, Any]] | None = None,
) -> list[Conflict]:
    """只做静态检查：不跑测试、不跑实验、不调模型。"""
    base = Path(root or PROJECT_ROOT)
    index = code_intel.build_index(base)
    conflicts: list[Conflict] = []

    for step in plan.get("steps") or []:
        raw = str(step.get("path") or "")
        resolved = _resolve_inside(raw, base)
        if resolved is None:
            conflicts.append(
                Conflict("out_of_workspace", True, f"路径越界或非法：{raw}", EXIT_INSUFFICIENT)
            )
            continue
        if step.get("action") == "create":
            if resolved.exists():
                conflicts.append(
                    Conflict("target_exists", True, f"要新建的文件已存在：{raw}", EXIT_INSUFFICIENT)
                )
            continue
        if not resolved.exists():
            conflicts.append(
                Conflict("target_missing", True, f"要修改的文件不存在：{raw}", EXIT_INSUFFICIENT)
            )
            continue
        # 计划点名的符号必须真的定义在这个文件里，否则改的是"想象中的代码"
        text = str(step.get("reason") or "") + " " + str(plan.get("task") or "")
        symbols = {
            symbol.name
            for symbols in index.symbols.values()
            for symbol in symbols
            if symbol.path == raw.replace("\\", "/")
        }
        named = [name for name in symbols if name in text]
        if symbols and not named and len(symbols) > 1:
            conflicts.append(
                Conflict(
                    "symbol_missing",
                    True,
                    f"{raw} 里没有匹配计划描述的符号（该文件定义了 {len(symbols)} 个）",
                    EXIT_INSUFFICIENT,
                )
            )

    for experience in experiences or []:
        paths = list(experience.get("changed_paths") or [])
        gone = [p for p in paths if not (base / p).exists()]
        recorded = str(experience.get("repo_commit") or "")
        if gone:
            conflicts.append(
                Conflict(
                    "stale_experience",
                    True,
                    f"经验引用的文件已不存在：{gone}（经验失效，不该再生效）",
                    EXIT_STALE,
                )
            )
        elif recorded and any(_content_changed_since(p, recorded, base) for p in paths):
            # 关键：判据是"经验引用的文件内容变了"，不是"仓库有新提交"——
            # 后者几乎每次都成立，用它当失效条件等于把所有经验一次作废。
            conflicts.append(
                Conflict(
                    "stale_experience",
                    True,
                    f"经验来自 {recorded}，它引用的文件此后已被改动，需重新确认",
                    EXIT_STALE,
                )
            )
    return conflicts


def needs_experiment(
    options: list[dict[str, Any]] | None, static_conflicts: list[Conflict]
) -> tuple[bool, str]:
    """只有"静态全过 + 存在两个可行方案"才值得跑实验。

    这条规则是确定性的：静态冲突还没解决就去跑实验，等于用最贵的手段去查最便宜的问题。
    """
    if static_conflicts:
        return False, "静态冲突未解决，先做静态处理"
    if not options or len(options) < 2:
        return False, "只有一个候选方案，没有可对照的对象"
    return True, f"{len(options)} 个方案都通过静态检查，行为差异只能靠跑实验分辨"


def resolve(
    plan: dict[str, Any],
    root: Path | None = None,
    experiences: list[dict[str, Any]] | None = None,
    options: list[dict[str, Any]] | None = None,
    experiments_allowed: int = 1,
) -> ConflictVerdict:
    """确定性的分流入口：静态 → 实验 → ok。"""
    static = detect_static_conflicts(plan, root, experiences)
    require, reason = needs_experiment(options, static)
    verdict = ConflictVerdict(
        static_conflicts=[asdict(item) for item in static],
        experiment={"required": require, "reason": reason},
        experiments_allowed=max(0, experiments_allowed),
        experiments_requested=1 if require else 0,
    )
    if static:
        # 先出静态冲突的结论：stale 优先于 insufficient（失效经验要显式作废）
        verdict.exit = (
            EXIT_STALE if any(c.exit == EXIT_STALE for c in static) else EXIT_INSUFFICIENT
        )
    elif require:
        verdict.exit = EXIT_EXPERIMENT
    else:
        verdict.exit = EXIT_OK
    return verdict


__all__ = [
    "Conflict",
    "ConflictVerdict",
    "EXIT_EXPERIMENT",
    "EXIT_INSUFFICIENT",
    "EXIT_OK",
    "EXIT_STALE",
    "STATIC_EXITS",
    "detect_static_conflicts",
    "needs_experiment",
    "resolve",
]
