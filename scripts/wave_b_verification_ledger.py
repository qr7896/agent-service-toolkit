from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def completed_commits(path: Path) -> set[str]:
    return {str(row["commit"]) for row in read_rows(path)}


def next_candidate(queue: Path, ledger: Path) -> dict[str, object] | None:
    payload = json.loads(queue.read_text(encoding="utf-8"))
    done = completed_commits(ledger)
    for candidate in payload["eligible_for_verification"]:
        if str(candidate["commit"]) not in done:
            return candidate
    return None


def append_result(ledger: Path, result: dict[str, object]) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("queue", type=Path)
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args()
    candidate = next_candidate(args.queue, args.ledger)
    print(json.dumps(candidate, sort_keys=True) if candidate else "null")


if __name__ == "__main__":
    main()
