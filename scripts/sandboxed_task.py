"""在隔离副本里跑一次 Coding Agent 任务（阶段 19）。

    python scripts/sandboxed_task.py --task "修复 calc.py 的 add" [--keep] [--agent]
    python scripts/sandboxed_task.py --task "..." --no-agent   # 只建副本，验证隔离

不带 --agent 时只创建副本、打印它的位置，用来确认隔离与回收是否正常，不调用任何 LLM。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from agents.workspace import create_sandbox, reclaim_sandbox, sandbox_env  # noqa: E402

RUNNER = """
import asyncio, json, sys
from langchain_core.messages import HumanMessage
from agents.coding_agent import coding_agent
from core import settings

async def main():
    out = await coding_agent.ainvoke(
        {"messages": [HumanMessage(content=sys.argv[1])]},
        {"configurable": {"model": settings.DEFAULT_MODEL, "thread_id": "sandboxed-task"},
         "recursion_limit": 80},
    )
    print(json.dumps({"status": (out.get("trajectory") or {}).get("status", "")}, ensure_ascii=False))

asyncio.run(main())
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a coding task inside an isolated copy")
    parser.add_argument("--task", required=True, help="任务描述")
    parser.add_argument("--name", default="task", help="副本名字（同名会被覆盖）")
    parser.add_argument("--keep", action="store_true", help="保留副本以便排查")
    parser.add_argument("--no-agent", action="store_true", help="只建副本，不调用 LLM")
    args = parser.parse_args()

    sandbox = create_sandbox(args.name)
    print(f"sandbox: {sandbox}")
    try:
        if not args.no_agent:
            proc = subprocess.run(
                [sys.executable, "-c", RUNNER, args.task],
                cwd=str(sandbox),
                env=sandbox_env(sandbox),
                capture_output=True,
                text=True,
                timeout=1800,
            )
            print(proc.stdout.strip()[-800:])
            if proc.returncode != 0:
                print(proc.stderr.strip()[-800:], file=sys.stderr)
    finally:
        if args.keep:
            print("kept (remove it manually when done)")
        else:
            reclaim_sandbox(sandbox)
            print("sandbox reclaimed")


if __name__ == "__main__":
    main()
