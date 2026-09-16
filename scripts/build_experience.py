"""把阶段 14 的轨迹 JSONL 灌进阶段 15 的经验库，并打印统计。

    python scripts/build_experience.py                      # 用默认路径
    python scripts/build_experience.py --db .codex/experience/experience.db
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from agents.experience import DEFAULT_EXPERIENCE_PATH, ExperienceStore  # noqa: E402
from agents.trajectory import DEFAULT_TRAJECTORY_PATH  # noqa: E402


def read_trajectories(path: Path) -> list[dict]:
    records: list[dict] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            records.append(item)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Build experience store from trajectories")
    parser.add_argument("--trajectories", type=Path, default=DEFAULT_TRAJECTORY_PATH)
    parser.add_argument("--db", type=Path, default=DEFAULT_EXPERIENCE_PATH)
    args = parser.parse_args()

    records = read_trajectories(args.trajectories)
    written = 0
    with ExperienceStore(args.db) as store:
        for record in records:
            written += len(store.record_trajectory(record))
        stats = store.stats()
    print(
        json.dumps(
            {"trajectories_read": len(records), "experiences_written": written, **stats},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
