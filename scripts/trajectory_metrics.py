"""读取轨迹，输出基础指标 + **盲区指标**。

盲区指标回答的是"门控在这个仓库上是不是已经失效了"：

  ast_parse_failure_rate  —— AST 解析失败的文件占比。索引看不见的文件越多，
                             门控拿到的 target 证据越假（"目标未知"其实是"读不到"）。
  unknown_symbol_rate     —— 计划步骤点名的符号在目标文件里找不到的比例。
                             它高说明模型在改"想象中的代码"，或者索引与仓库不同步。
  gate_pass_rate / exits  —— 证据门控的通过率与三类出口分布。
  conflict_exits          —— 冲突分流的出口分布（静态 vs 需要实验）。

没有这些数，门控退化时只能靠"感觉不对"。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from agents import code_intel  # noqa: E402
from agents.trajectory import DEFAULT_TRAJECTORY_PATH, aggregate_trajectories  # noqa: E402

PROJECT_ROOT = PROJECT_DIR


def read_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            records.append(item)
    return records


def blind_spot_metrics(records: list[dict], root: Path = PROJECT_ROOT) -> dict:
    """从轨迹 + 代码索引算盲区指标。纯统计，不调模型。"""
    index = code_intel.build_index(root)
    symbols_by_path: dict[str, set[str]] = {}
    for name, symbols in index.symbols.items():
        for symbol in symbols:
            symbols_by_path.setdefault(symbol.path, set()).add(name)

    steps = 0
    unknown = 0
    for record in records:
        for step in (record.get("plan") or {}).get("steps") or []:
            steps += 1
            path = str(step.get("path") or "").replace("\\", "/")
            if not (root / path).exists():
                unknown += 1
                continue
            names = symbols_by_path.get(path, set())
            text = f"{step.get('reason') or ''} {record.get('task') or ''}"
            if names and not any(name in text for name in names):
                unknown += 1

    gates = [r.get("evidence_gate") or {} for r in records]
    gates = [g for g in gates if g]
    passes = sum(1 for g in gates if g.get("passed"))
    exits: dict[str, int] = {}
    for g in gates:
        key = str(g.get("exit") or "unknown")
        exits[key] = exits.get(key, 0) + 1
    conflicts: dict[str, int] = {}
    for record in records:
        key = str((record.get("conflicts") or {}).get("exit") or "none")
        conflicts[key] = conflicts.get(key, 0) + 1

    return {
        "tasks": len(records),
        "ast_parse_failure_rate": round(len(index.parse_failures) / index.files_seen, 4)
        if index.files_seen
        else 0.0,
        "ast_parse_failure_files": index.parse_failures[:10],
        "unknown_symbol_steps": unknown,
        "unknown_symbol_rate": round(unknown / steps, 4) if steps else 0.0,
        "gate_runs": len(gates),
        "gate_pass_rate": round(passes / len(gates), 4) if gates else None,
        "gate_exits": exits,
        "conflict_exits": conflicts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate coding-agent trajectory JSONL")
    parser.add_argument("--path", type=Path, default=DEFAULT_TRAJECTORY_PATH, help="JSONL trajectory path")
    parser.add_argument("--blind-spots", action="store_true", help="额外输出盲区指标")
    args = parser.parse_args()
    report = aggregate_trajectories(args.path)
    if args.blind_spots:
        report["blind_spots"] = blind_spot_metrics(read_records(args.path))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
