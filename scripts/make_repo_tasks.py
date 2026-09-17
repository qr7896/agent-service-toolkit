"""从本仓库的真实修复历史生成 SWE 风格任务（doc 03 §11 的替代数据源）。

为什么这样做：真实 GitHub issue 数据集（SWE-bench 等）体积大、需要联网下载，而"自造任务"
又容易变成 demo。折中方案是**用本仓库自己的真实 bug 修复史**：每个任务都对应一次真实修复，
有明确的 buggy rev、修复 rev、以及可执行判据。

    python scripts/make_repo_tasks.py            # 生成 evals/tasks/repo_tasks.jsonl
    python scripts/make_repo_tasks.py --list     # 只看任务定义

文件内容直接从 git 里取（`git show <rev>:<path>`），所以仓库里不存重复源码，
新增任务也只是往 TASKS 里加一条——扩展是机械劳动，不需要人工誊写代码。

已知的 fixture 折中：为了让被测模块能独立导入，沙箱里放一个**空的** `src/agents/__init__.py`
（真实的那份会拉进整条 agent 链）。这不影响被测函数的语义，但要在结论里说明。
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT_DIR / "evals" / "tasks" / "repo_tasks.jsonl"

TEST_INPUT_FALLBACK = '''\
import importlib.util
import sys
from pathlib import Path

SRC = Path(__file__).parent / "src"


def _module():
    """按文件路径加载被测模块。

    不能用 `import agents.agent_workflow`：本项目是 editable 安装，`agents` 包会被
    setuptools 的 meta-path finder 截走，结果加载的是**工作区里的版本**而不是沙箱里的
    被测版本——那样任务就永远"通过"，等于没有判分。这个坑是实测发现的。
    """
    path = SRC / "agents" / "agent_workflow.py"
    spec = importlib.util.spec_from_file_location("agent_workflow_under_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["agent_workflow_under_test"] = module
    spec.loader.exec_module(module)
    return module


def test_input_from_messages():
    """服务端只传 messages：工作流必须能从里面取出用户输入。"""
    class Msg:
        __class__ = type("HumanMessage", (), {})

        def __init__(self, content):
            self.content = content

    msg = Msg("修一下 add")
    msg.__class__.__name__ = "HumanMessage"
    assert _module().user_input({"messages": [msg]}) == "修一下 add"


def test_explicit_input_wins():
    """显式传入的 workflow_input 优先于 messages。"""
    assert _module().user_input({"workflow_input": "显式", "messages": []}) == "显式"


def test_render_template_still_works():
    """回归用例：修复前就通过，修复后不能退步。"""
    assert _module().render_template("{input}-{previous}", "I", "P") == "I-P"
'''

TASKS: list[dict] = [
    {
        "instance_id": "repo__workflow_input_from_messages-1",
        "problem_statement": (
            "工作流通过服务端调用时收到空输入：输入只从 state['workflow_input'] 取，"
            "而服务端只传 messages。修复后应能从 messages 里取出用户输入，"
            "同时保留显式 workflow_input 的优先级。"
        ),
        # 修复提交是 3183ac9；这里必须取它的前一个提交，否则"buggy 版本"里已经有修复
        # （第一版写成 28ef9cb 就踩了这个坑——它其实比修复提交更新，任务因此永远通过）
        "buggy_rev": "59e9bdd",
        "gold_rev": "HEAD",
        "files": [
            "src/agents/agent_workflow.py",
            "src/agents/agent_config.py",
            "src/core/settings.py",
            "src/core/llm.py",
            "src/core/__init__.py",
        ],
        "extra_files": {"src/agents/__init__.py": ""},
        "test_file": "test_workflow_input.py",
        "test_code": TEST_INPUT_FALLBACK,
        "FAIL_TO_PASS": ["test_workflow_input.py::test_input_from_messages"],
        "PASS_TO_PASS": [
            "test_workflow_input.py::test_render_template_still_works",
        ],
    }
]


def show(rev: str, path: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(PROJECT_DIR), "show", f"{rev}:{path}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if out.returncode != 0:
        raise SystemExit(f"git show 失败：{rev}:{path} -> {out.stderr.strip()[:120]}")
    return out.stdout


def build(task: dict) -> dict:
    setup = {path: show(task["buggy_rev"], path) for path in task["files"]}
    setup.update(task.get("extra_files") or {})
    gold = {path: show(task["gold_rev"], path) for path in task["files"]}
    return {
        "instance_id": task["instance_id"],
        "repo": "qr7896/agent-service-toolkit",
        "base_commit": task["buggy_rev"],
        "problem_statement": task["problem_statement"],
        "setup_files": setup,
        "test_files": {task["test_file"]: task["test_code"]},
        "gold_sources": gold,
        "FAIL_TO_PASS": task["FAIL_TO_PASS"],
        "PASS_TO_PASS": task["PASS_TO_PASS"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate SWE-style tasks from this repo's history"
    )
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    if args.list:
        for task in TASKS:
            print(f"{task['instance_id']:44s} {task['buggy_rev']} -> {task['gold_rev']}")
        return
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as handle:
        for task in TASKS:
            handle.write(json.dumps(build(task), ensure_ascii=False) + "\n")
    print(f"已写入 {OUTPUT}（{len(TASKS)} 个任务，{OUTPUT.stat().st_size} 字节）")


if __name__ == "__main__":
    main()
