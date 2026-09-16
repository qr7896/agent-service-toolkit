"""读取 Coding Agent 的 JSONL 轨迹，输出基础评测指标。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from agents.trajectory import DEFAULT_TRAJECTORY_PATH, aggregate_trajectories  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate coding-agent trajectory JSONL")
    parser.add_argument("--path", type=Path, default=DEFAULT_TRAJECTORY_PATH, help="JSONL trajectory path")
    args = parser.parse_args()
    print(json.dumps(aggregate_trajectories(args.path), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
