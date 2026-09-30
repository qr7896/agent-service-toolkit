from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

TASK_REPO_URL = "https://github.com/SWE-bench/swe-bench-tasks.git"


def fetch_public_probe(url: str = TASK_REPO_URL) -> dict[str, object]:
    completed = subprocess.run(
        ["git", "ls-remote", url, "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    head_sha = completed.stdout.strip().split()[0]
    return {
        "transport": "git",
        "url": url,
        "reachable": True,
        "head_sha": head_sha,
    }


def write_probe(output: Path, probe: dict[str, object]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(probe, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Content-neutral network probe for isolated Wave B public task discovery."
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--url", default=TASK_REPO_URL)
    args = parser.parse_args()
    write_probe(args.output, fetch_public_probe(args.url))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
