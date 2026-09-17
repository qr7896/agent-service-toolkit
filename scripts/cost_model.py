"""实验 vs 静态判定的成本模型（读已有产物，不调 LLM）。

要回答的问题：**"每个冲突都跑一次沙箱 A/B"到底多贵？**

数据来源（都是本机真实跑出来的）：
  - `.codex/benchmark/report.json`：各组 A/B 的 `avg_estimated_tokens`
  - `.codex/trajectories/coding_agent.jsonl`：逐次运行的 `llm_calls` / `estimated_tokens`

口径说明：`estimated_tokens` 是"字符数 ÷ 3"的粗估（见 §4.22），只适合比较**相对量级**，
不是账单。实验成本按"同一任务跑两遍候选方案"估，验证（pytest）不消耗 token。

    python scripts/cost_model.py
    python scripts/cost_model.py --tasks 30 --conflict-rate 0.5
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
REPORT = PROJECT_DIR / ".codex" / "benchmark" / "report.json"
TRAJECTORIES = PROJECT_DIR / ".codex" / "trajectories" / "coding_agent.jsonl"


def read_report() -> dict:
    if not REPORT.exists():
        return {}
    try:
        return json.loads(REPORT.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def read_trajectories() -> list[dict]:
    if not TRAJECTORIES.exists():
        return []
    records = []
    for line in TRAJECTORIES.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict) and item.get("estimated_tokens"):
            records.append(item)
    return records


def _avg(values: list[int]) -> float:
    return round(sum(values) / len(values), 1) if values else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Experiments vs static checks: a token cost model")
    parser.add_argument("--tasks", type=int, default=30, help="待处理任务数（用于外推）")
    parser.add_argument("--conflict-rate", type=float, default=0.3, help="每个任务触发冲突的概率")
    parser.add_argument("--static-share", type=float, default=0.9, help="冲突中静态可判的比例")
    args = parser.parse_args()

    report = read_report()
    arms = report.get("arms") or {
        name: report.get(name) for name in ("baseline", "experience") if report.get(name)
    }
    rows = [row for row in (report.get("rows") or [])]

    print("== 实测的单次运行成本（estimated_tokens 粗估）==")
    per_run: list[int] = []
    for name, summary in arms.items():
        if not summary:
            continue
        print(
            f"  {name:20s} 任务 {summary.get('tasks', 0)} 个 | "
            f"平均 {summary.get('avg_estimated_tokens', 0):>10,.0f} tok | "
            f"平均 {summary.get('avg_llm_calls', 0):>5.1f} 次 LLM 调用"
        )
        if summary.get("avg_estimated_tokens"):
            per_run.append(int(summary["avg_estimated_tokens"]))
    for row in rows:  # 逐行数据更真实：能看到最贵的那次有多贵
        if row.get("estimated_tokens"):
            per_run.append(int(row["estimated_tokens"]))
    if not per_run:
        trajectories = read_trajectories()
        per_run = [int(item["estimated_tokens"]) for item in trajectories]
        if per_run:
            print(f"  （来自轨迹文件，共 {len(per_run)} 次运行）")

    if not per_run:
        print("没有可用的实测数据：先跑一次基准（evals/coding_benchmark.py）再回来算。")
        return

    typical = round(_avg(sorted(per_run)[: max(1, len(per_run) // 2)]))  # 取较便宜的一半当"典型"
    worst = max(per_run)
    experiment = typical * 2  # 两个候选方案各跑一遍；验证本身不花 token

    print("\n== 单次冲突的解决成本 ==")
    print("  静态判定（路径/符号/版本哈希）：0 token，0 次 LLM 调用")
    print(f"  沙箱 A/B（跑两个候选方案）：约 {experiment:,} tok（= 典型单次 {typical:,} × 2）")
    print(f"  最坏情况（本机实测单次峰值 {worst:,} tok → 一次实验 ≈ {worst * 2:,} tok）")
    print("  倍数关系：一次实验 ≈ 静态判定的无穷倍（静态是 0），量级差 2 个数量级起步")

    conflicts = args.tasks * args.conflict_rate
    static_part = conflicts * args.static_share
    experiment_part = conflicts - static_part
    naive = conflicts * experiment
    static_first = experiment_part * experiment
    print(
        f"\n== 外推（{args.tasks} 任务，冲突率 {args.conflict_rate:.0%}，其中静态可判 {args.static_share:.0%}）=="
    )
    print(f"  冲突数：{conflicts:.0f} 个")
    print(f"  全部走实验：约 {naive:,.0f} tok")
    print(
        f"  静态优先：  约 {static_first:,.0f} tok（省下 {naive - static_first:,.0f} tok，{(1 - static_first / naive):.0%}）"
    )
    print("\n注意：这是量级估算，不是账单；冲突率与静态可判比例是假设，跑真实任务时应实测。")


if __name__ == "__main__":
    main()
