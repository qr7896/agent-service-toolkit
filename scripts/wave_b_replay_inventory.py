from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

REPAIR_RE = re.compile(r"\b(fix(?:es|ed|ing)?|bug|regression|error|exception|crash|incorrect|wrong|fail(?:s|ed|ure)?|issue)\b", re.I)
TEST_RE = re.compile(r"(^|/)(tests?)(/|_)|(^|/)test_[^/]*\.py$", re.I)


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True, encoding="utf-8", errors="replace")


def inventory(repo: Path, limit: int | None = None) -> list[dict[str, object]]:
    raw = git(repo, "log", "--no-merges", "--format=@@@%H%x09%s", "--name-only")
    rows: list[dict[str, object]] = []
    current_sha = ""
    current_subject = ""
    files: list[str] = []

    def consider() -> None:
        if not current_sha or not REPAIR_RE.search(current_subject):
            return
        tests = [x for x in files if TEST_RE.search(x)]
        production = [x for x in files if x.endswith(".py") and x not in tests]
        if tests and production:
            rows.append({"commit": current_sha, "subject": current_subject, "production_files": production, "test_files": tests})

    for line in raw.splitlines():
        if line.startswith("@@@"):
            consider()
            if limit is not None and len(rows) >= limit:
                break
            header = line[3:].split("\t", 1)
            current_sha = header[0]
            current_subject = header[1] if len(header) > 1 else ""
            files = []
        elif line:
            files.append(line)
    else:
        consider()
    return rows[:limit] if limit is not None else rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = {"repo": str(args.repo), "head": git(args.repo, "rev-parse", "HEAD").strip(), "candidates": inventory(args.repo, args.limit)}
    payload = json.dumps(data, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
