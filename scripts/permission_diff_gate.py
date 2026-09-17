"""CI 权限差异门禁：改动碰到权限相关代码时必须显式承认 + 跑权限专项验收。

为什么要这道门：本项目最贵的事故不是"算错"，而是**权限被悄悄放宽**——
路径约束、工具白名单、HITL 审批、沙箱隔离，任何一处改松，其他所有测试都会照常通过。
普通 CI（test / deploy / live-smoke）看不出这类变化，因为功能是对的、权限是错的。

    python scripts/permission_diff_gate.py                     # 与 origin/main 比
    python scripts/permission_diff_gate.py --base HEAD~1
    python scripts/permission_diff_gate.py --files a.py b.py   # 直接给文件列表（测试用）
    python scripts/permission_diff_gate.py --ack 1             # 已人工确认

碰到敏感文件时：打印清单 → 跑权限专项验收 → 没有 `--ack` 就退出码 1。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]

# 权限相关文件：改了这些就必须人工确认
SENSITIVE_PATTERNS = {
    "src/agents/code_tools.py": "文件路径约束 / 写工具黑名单",
    "src/agents/coding_agent.py": "HITL 审批闸门 / 写权限开关",
    "src/agents/workspace.py": "沙箱隔离与回收",
    "src/agents/conflict.py": "冲突分流（静态 vs 实验）",
    "src/agents/agent_config.py": "工具白名单校验",
    "src/agents/agents.py": "可配置 Agent 的工具白名单注册",
    "src/agents/test_tools.py": "命令执行范围（只允许 pytest）",
    "scripts/verify_container.ps1": "容器挂载与数据卷",
}
SENSITIVE_PREFIXES = {
    "config/agents/": "可配置 Agent 的工具白名单",
    ".github/workflows/": "CI 门禁本身",
}

# 碰到敏感改动就要跑的权限专项验收
PERMISSION_CHECKS = [
    "lg_practice/day13_hitl_check.py",
    "lg_practice/day19_sandbox_check.py",
    "lg_practice/day32_conflict_classify_check.py",
    "lg_practice/day33_hitl_durable_check.py",
]


def changed_files(base: str) -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(PROJECT_DIR), "diff", "--name-only", f"{base}...HEAD"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if proc.returncode != 0:
        print(f"git diff 失败：{proc.stderr.strip()[:200]}", file=sys.stderr)
        return []
    return [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]


def sensitive_hits(files: list[str]) -> list[tuple[str, str]]:
    hits: list[tuple[str, str]] = []
    for path in files:
        normalized = path.replace("\\", "/")
        if normalized in SENSITIVE_PATTERNS:
            hits.append((normalized, SENSITIVE_PATTERNS[normalized]))
            continue
        for prefix, reason in SENSITIVE_PREFIXES.items():
            if normalized.startswith(prefix):
                hits.append((normalized, reason))
                break
    return hits


def run_checks(checks: list[str]) -> bool:
    ok = True
    for rel in checks:
        path = PROJECT_DIR / rel
        if not path.exists():
            print(f"  跳过（不存在）：{rel}")
            continue
        proc = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=1800,
            cwd=str(PROJECT_DIR / "src"),
        )
        status = "OK" if proc.returncode == 0 else "FAIL"
        print(f"  [{status}] {rel}")
        ok = ok and proc.returncode == 0
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Permission-change diff gate")
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--files", nargs="*", default=None, help="直接给文件列表（跳过 git）")
    parser.add_argument("--ack", action="store_true", help="已人工确认过权限变更")
    parser.add_argument("--skip-checks", action="store_true")
    args = parser.parse_args()

    files = args.files if args.files is not None else changed_files(args.base)
    hits = sensitive_hits(files)
    print(f"变更文件 {len(files)} 个，其中权限相关 {len(hits)} 个")
    if not hits:
        print("没有权限相关改动，门禁通过")
        return 0

    print("权限相关改动：")
    for path, reason in hits:
        print(f"  - {path}（{reason}）")
    checks_ok = True
    if not args.skip_checks:
        print("跑权限专项验收：")
        checks_ok = run_checks(PERMISSION_CHECKS)
    if not checks_ok:
        print("权限专项验收未通过，门禁失败", file=sys.stderr)
        return 1
    if not args.ack:
        print(
            "检测到权限相关改动且尚未确认：请人工确认后加 --ack 再跑一次"
            "（确认内容：权限是被收紧还是放宽、放宽是否必要）",
            file=sys.stderr,
        )
        return 1
    print("权限变更已确认，门禁通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
