from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_commits(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data["candidates"])


def prefixes(path: Path | None) -> set[str]:
    if path is None:
        return set()
    return {line.strip().lower() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def excluded(commit: str, blocked: set[str]) -> bool:
    value = commit.lower()
    return any(value.startswith(item) or item.startswith(value) for item in blocked)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inventories", nargs="+", type=Path)
    parser.add_argument("--exclude-commits", type=Path)
    parser.add_argument("--limit", type=int, default=18)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    blocked = prefixes(args.exclude_commits)
    audit: list[dict[str, object]] = []
    eligible: list[dict[str, object]] = []
    seen: set[str] = set()

    for inventory_path in args.inventories:
        for candidate in load_commits(inventory_path):
            commit = str(candidate["commit"])
            reason = "eligible_for_verification"
            if commit in seen:
                reason = "duplicate_commit"
            elif excluded(commit, blocked):
                reason = "excluded_commit_overlap"
            seen.add(commit)
            row = {"inventory": str(inventory_path), "commit": commit, "decision": reason}
            audit.append(row)
            if reason == "eligible_for_verification" and len(eligible) < args.limit:
                eligible.append(candidate)

    payload = {
        "selection_limit": args.limit,
        "eligible_for_verification_count": len(eligible),
        "eligible_for_verification": eligible,
        "audit": audit,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
