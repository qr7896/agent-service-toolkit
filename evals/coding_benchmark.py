"""阶段 18：Baseline vs +Experience 的 Coding Benchmark。

设计与口径（先说清楚，避免拿单个案例讲故事）：

  1. 同一批任务跑两遍。**第一遍是冷启动**（`record_experience=False`、不检索），
     把这些轨迹沉淀成经验；**第二遍是热启动**（同一个经验库，开启检索）。
     两遍的任务、提示词、模型完全一致，唯一变量是"有没有经验可查"。
  2. 成败由**独立判分**决定：跑完以后自己再执行一次 pytest，不采信 Agent 自己
     的 tester 结论——否则"Agent 说成功"就变成"成功"了。
  3. 指标来自阶段 14 的轨迹：成功率、首次通过率、平均 attempts、平均工具调用数、
     平均耗时；另外记录每次运行命中的经验条数，用来证明第二遍真的查到了东西。
  4. 样本量很小（默认 6 个任务 × 2 遍）。这里只能给方向性证据，不宣称统计显著性。

用法：
    python evals/coding_benchmark.py --list
    python evals/coding_benchmark.py --limit 1          # 冒烟
    python evals/coding_benchmark.py                    # 全量
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from langchain_core.messages import HumanMessage  # noqa: E402

from agents.coding_agent import coding_agent  # noqa: E402
from core import settings  # noqa: E402

RECURSION_LIMIT = 80  # 与 day12 一致；40 会在一次正常的多轮工具循环里就触发上限

SANDBOX = PROJECT_DIR / "_eval_sandbox"
EVAL_DATA = PROJECT_DIR / ".codex" / "benchmark"
REPORT = EVAL_DATA / "report.json"

# EGCP 实验的四组对照（doc 03 §9）：同任务、同模型、同提示词，只改检索/证据策略
ARMS: dict[str, dict] = {
    "A_files_only": {"disable_search_code": True, "planner_recon_steps": 2},
    "B_search": {"planner_recon_steps": 2},
    "C_codeintel": {"code_intel_tools": True, "planner_recon_steps": 2},
    "D_codeintel_gate": {"code_intel_tools": True, "evidence_gate": True, "planner_recon_steps": 2},
}


@dataclass
class Task:
    name: str
    kind: str
    prompt: str
    source_file: str
    source: str
    test_file: str
    test: str
    files: dict[str, str] = field(default_factory=dict)


TASKS: list[Task] = [
    Task(
        name="stats_mean_empty",
        kind="edge_case_guard",
        prompt="修复 src/stats_util.py 的 mean：空列表应当返回 0.0，而不是抛异常。只改必要的代码。",
        source_file="stats_util.py",
        source=(
            "def mean(values):\n"
            "    return sum(values) / len(values)\n"
        ),
        test_file="test_stats_util.py",
        test=(
            "from stats_util import mean\n\n\n"
            "def test_mean_normal():\n"
            "    assert mean([1, 2, 3]) == 2\n\n\n"
            "def test_mean_empty():\n"
            "    assert mean([]) == 0.0\n"
        ),
    ),
    Task(
        name="stats_median_even",
        kind="edge_case_guard",
        prompt="修复 src/stats_util.py 的 median：偶数个元素时应取中间两个的平均值。只改必要的代码。",
        source_file="stats_util.py",
        source=(
            "def median(values):\n"
            "    ordered = sorted(values)\n"
            "    return ordered[len(ordered) // 2]\n"
        ),
        test_file="test_stats_util.py",
        test=(
            "from stats_util import median\n\n\n"
            "def test_median_odd():\n"
            "    assert median([3, 1, 2]) == 2\n\n\n"
            "def test_median_even():\n"
            "    assert median([1, 2, 3, 4]) == 2.5\n"
        ),
    ),
    Task(
        name="math_safe_divide",
        kind="edge_case_guard",
        prompt="修复 src/math_util.py 的 safe_divide：除数为 0 时应返回 0.0。只改必要的代码。",
        source_file="math_util.py",
        source=(
            "def safe_divide(a, b):\n"
            "    return a / b\n"
        ),
        test_file="test_math_util.py",
        test=(
            "from math_util import safe_divide\n\n\n"
            "def test_divide_normal():\n"
            "    assert safe_divide(6, 3) == 2\n\n\n"
            "def test_divide_by_zero():\n"
            "    assert safe_divide(1, 0) == 0.0\n"
        ),
    ),
    Task(
        name="text_slug_lowercase",
        kind="case_normalization",
        prompt="修复 src/text_util.py 的 slugify：结果应当全部小写，空格换成连字符。只改必要的代码。",
        source_file="text_util.py",
        source=(
            "def slugify(text):\n"
            "    return text.replace(' ', '-')\n"
        ),
        test_file="test_text_util.py",
        test=(
            "from text_util import slugify\n\n\n"
            "def test_slugify_spaces():\n"
            "    assert slugify('hello world') == 'hello-world'\n\n\n"
            "def test_slugify_case():\n"
            "    assert slugify('Hello World') == 'hello-world'\n"
        ),
    ),
    Task(
        name="text_wrap_off_by_one",
        kind="off_by_one",
        prompt="修复 src/text_util.py 的 chunk：每段最多 width 个字符，不能多。只改必要的代码。",
        source_file="text_util.py",
        source=(
            "def chunk(text, width):\n"
            "    return [text[i:i + width + 1] for i in range(0, len(text), width)]\n"
        ),
        test_file="test_text_util.py",
        test=(
            "from text_util import chunk\n\n\n"
            "def test_chunk_exact():\n"
            "    assert chunk('abcdef', 3) == ['abc', 'def']\n\n\n"
            "def test_chunk_max_width():\n"
            "    assert all(len(part) <= 4 for part in chunk('abcdefgh', 4))\n"
        ),
    ),
    Task(
        name="math_clamp_bounds",
        kind="off_by_one",
        prompt="修复 src/math_util.py 的 clamp：小于下界取下界、大于上界取上界，界内原样返回。只改必要的代码。",
        source_file="math_util.py",
        source=(
            "def clamp(value, low, high):\n"
            "    if value < low:\n"
            "        return high\n"
            "    if value > high:\n"
            "        return low\n"
            "    return value\n"
        ),
        test_file="test_math_util.py",
        test=(
            "from math_util import clamp\n\n\n"
            "def test_clamp_inside():\n"
            "    assert clamp(5, 0, 10) == 5\n\n\n"
            "def test_clamp_below():\n"
            "    assert clamp(-1, 0, 10) == 0\n\n\n"
            "def test_clamp_above():\n"
            "    assert clamp(99, 0, 10) == 10\n"
        ),
    ),
]


def setup_task(task: Task) -> Path:
    """每个任务一个独立沙箱：src/ 放被测代码，测试放在沙箱根目录。

    新建的文件必须 `git add -N`（intent to add）——否则 `git_diff` 看不到它们，
    Reviewer 会因为"diff 里没有目标文件"而否决一次本来正确的修复。
    """
    sandbox = SANDBOX / task.name
    if sandbox.exists():
        shutil.rmtree(sandbox)
    (sandbox / "src").mkdir(parents=True, exist_ok=True)
    source = sandbox / "src" / task.source_file
    test = sandbox / task.test_file
    source.write_text(task.source, encoding="utf-8")
    test.write_text(task.test, encoding="utf-8")
    subprocess.run(
        ["git", "add", "-N", str(source.relative_to(PROJECT_DIR)), str(test.relative_to(PROJECT_DIR))],
        cwd=str(PROJECT_DIR),
        capture_output=True,
        text=True,
    )
    return sandbox


def unstage_sandbox() -> None:
    subprocess.run(["git", "reset", "--", SANDBOX.name], cwd=str(PROJECT_DIR), capture_output=True)
    subprocess.run(
        ["git", "restore", "--staged", "--", SANDBOX.name], cwd=str(PROJECT_DIR), capture_output=True
    )


def grade(task: Task, sandbox: Path) -> tuple[bool, str]:
    """独立判分：自己再跑一次 pytest，不看 Agent 自报的结论。"""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", task.test_file],
        cwd=str(sandbox),
        capture_output=True,
        text=True,
        timeout=180,
    )
    tail = (proc.stdout or "").strip().splitlines()
    return proc.returncode == 0, (tail[-1] if tail else (proc.stderr or "").strip()[:120])


def config_for(task: Task, arm: str, model: str) -> dict:
    conf = {
        "model": model,
        "test_path": f"{SANDBOX.name}/{task.name}/{task.test_file}",
        "review_path": f"{SANDBOX.name}/{task.name}",
        "allow_write": True,
        "require_approval": False,
        "trajectory_path": str(EVAL_DATA / "trajectories.jsonl"),
        "experience_path": str(EVAL_DATA / "experience.db"),
        "experience_chroma_path": str(EVAL_DATA / "chroma"),
        # 这些任务在需求里就点明了文件，不需要多轮侦察；两臂用同一设置，保持可比
        "planner_recon_steps": 1,
    }
    if arm == "baseline":
        # 基线 = "没有经验可查"，但仍然把这次的轨迹沉淀下来，
        # 否则处理臂没有任何历史经验可检索，实验就没法比。
        conf["experience_top_k"] = 0
    # EGCP 对照臂：把策略覆盖叠加在上面（A 组会移除 search_code）
    conf.update(ARMS.get(arm, {}))
    return {"configurable": conf, "recursion_limit": RECURSION_LIMIT}


def read_trajectory(path: Path) -> dict:
    if not path.exists():
        return {}
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    try:
        return json.loads(lines[-1]) if lines else {}
    except json.JSONDecodeError:
        return {}


async def run_one(task: Task, arm: str, model: str) -> dict:
    sandbox = setup_task(task)
    config = config_for(task, arm, model)
    before = read_trajectory(EVAL_DATA / "trajectories.jsonl")
    started = time.perf_counter()
    error = ""
    try:
        await coding_agent.ainvoke(
            {"messages": [HumanMessage(content=task.prompt)]},
            config={"configurable": {**config["configurable"], "thread_id": f"{arm}-{task.name}"},
                    "recursion_limit": RECURSION_LIMIT},
        )
    except Exception as exc:  # 单任务失败不该中断整场基准
        error = f"{type(exc).__name__}: {exc}"[:200]
    elapsed = round(time.perf_counter() - started, 1)

    passed, summary = grade(task, sandbox)
    trajectory = read_trajectory(EVAL_DATA / "trajectories.jsonl")
    fresh = trajectory if trajectory.get("id") != before.get("id") else {}
    unstage_sandbox()
    shutil.rmtree(sandbox, ignore_errors=True)
    return {
        "task": task.name,
        "kind": task.kind,
        "arm": arm,
        "passed": passed,
        "grade_summary": summary,
        "agent_status": fresh.get("status", ""),
        "attempts": int(fresh.get("attempts") or 0),
        "tool_calls": sum((fresh.get("tool_call_counts") or {}).values()),
        "experience_hits": len(fresh.get("experience_hits") or []),
        # 阶段 21 起每次调用都会记账，基准必须把成本一起报出来：
        # 只比成功率不比成本，等于没验证"更省"这个主张。
        "llm_calls": int(fresh.get("llm_calls") or 0),
        "estimated_tokens": int(fresh.get("estimated_tokens") or 0),
        "model_used": str(fresh.get("model_used") or fresh.get("model") or ""),
        "duration_seconds": float(fresh.get("duration_seconds") or elapsed),
        "error": error,
    }


def summarize(rows: list[dict]) -> dict:
    """汇总一行一个任务的记录。所有字段都用 .get() 取值——旧报告缺字段时不能崩，
    因为"重算历史报告"是很常见的动作。
    """
    if not rows:
        return {}
    n = len(rows)
    return {
        "tasks": n,
        "graded_pass_rate": round(sum(bool(r.get("passed")) for r in rows) / n, 3),
        "first_try_pass_rate": round(
            sum(bool(r.get("passed")) and int(r.get("attempts") or 0) <= 1 for r in rows) / n, 3
        ),
        "avg_attempts": round(sum(int(r.get("attempts") or 0) for r in rows) / n, 2),
        "avg_tool_calls": round(sum(int(r.get("tool_calls") or 0) for r in rows) / n, 2),
        "avg_llm_calls": round(sum(r.get("llm_calls", 0) for r in rows) / n, 2),
        "total_estimated_tokens": sum(r.get("estimated_tokens", 0) for r in rows),
        "avg_estimated_tokens": round(sum(r.get("estimated_tokens", 0) for r in rows) / n, 1),
        "avg_duration_seconds": round(
            sum(float(r.get("duration_seconds") or 0.0) for r in rows) / n, 1
        ),
        "runs_with_experience": sum(1 for r in rows if int(r.get("experience_hits") or 0) > 0),
        "agent_reported_success": sum(
            1 for r in rows if str(r.get("agent_status") or "") == "succeeded"
        ),
    }


async def main_async(limit: int | None, model: str) -> int:
    tasks = TASKS[:limit] if limit else TASKS
    EVAL_DATA.mkdir(parents=True, exist_ok=True)
    for stale in ("trajectories.jsonl", "experience.db"):
        (EVAL_DATA / stale).unlink(missing_ok=True)
    shutil.rmtree(EVAL_DATA / "chroma", ignore_errors=True)
    shutil.rmtree(SANDBOX, ignore_errors=True)
    unstage_sandbox()

    rows: list[dict] = []
    for arm in ("baseline", "experience"):
        print(f"\n=== arm: {arm} ===")
        for task in tasks:
            row = await run_one(task, arm, model)
            rows.append(row)
            print(
                f"  {task.name:24s} passed={str(row['passed']):5s} attempts={row['attempts']} "
                f"tools={row['tool_calls']:3d} llm={row['llm_calls']:3d} "
                f"tok~{row['estimated_tokens']:6d} hits={row['experience_hits']} "
                f"{row['duration_seconds']}s "
                f"{row['error']}"
            )
    shutil.rmtree(SANDBOX, ignore_errors=True)

    report = {
        "model": model,
        "task_count": len(tasks),
        "baseline": summarize([r for r in rows if r["arm"] == "baseline"]),
        "experience": summarize([r for r in rows if r["arm"] == "experience"]),
        "rows": rows,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== 汇总 ===")
    print(json.dumps({k: report[k] for k in ("baseline", "experience")}, ensure_ascii=False, indent=2))
    print(f"\n明细：{REPORT}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Coding benchmark: baseline vs experience memory")
    parser.add_argument("--limit", type=int, default=None, help="只跑前 N 个任务（冒烟用）")
    parser.add_argument("--model", default=settings.DEFAULT_MODEL)
    parser.add_argument("--list", action="store_true", help="列出任务后退出")
    args = parser.parse_args()
    if args.list:
        for task in TASKS:
            print(f"{task.name:24s} {task.kind}")
        return
    raise SystemExit(asyncio.run(main_async(args.limit, args.model)))


if __name__ == "__main__":
    main()
