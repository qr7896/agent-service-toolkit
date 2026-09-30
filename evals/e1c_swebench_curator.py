from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXCLUDED_REPOS = {"more-itertools/more-itertools"}


def _rank(row: dict[str, Any]) -> str:
    key = f"{row['instance_id']}|{row['repo']}|{row['base_commit']}"
    return hashlib.sha256(key.encode()).hexdigest()


def curate(rows: list[dict[str, Any]], n: int = 30) -> dict[str, Any]:
    eligible = []
    seen_commits: set[str] = set()
    for row in sorted(rows, key=_rank):
        commit = str(row.get("base_commit", ""))
        if row.get("repo") in EXCLUDED_REPOS or not commit or commit in seen_commits:
            continue
        if not row.get("FAIL_TO_PASS") or not row.get("PASS_TO_PASS"):
            continue
        seen_commits.add(commit)
        eligible.append(
            {
                "instance_id": row["instance_id"],
                "repo": row["repo"],
                "base_commit": commit,
                "version": row.get("version"),
                "rank_sha256": _rank(row),
            }
        )
        if len(eligible) == n:
            break
    return {
        "schema_version": "e1c-swebench-verified-curation-v1",
        "source": "SWE-bench/SWE-bench_Verified:test",
        "selection": "sha256(instance_id|repo|base_commit), ascending; first eligible",
        "requested": n,
        "admitted_metadata_candidates": len(eligible),
        "candidates": eligible,
        "claim_boundary": "metadata selection only; Base-Fail/Gold-Pass still require harness verification",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--n", type=int, default=30)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    result = curate(rows, args.n)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"requested": args.n, "selected": len(result["candidates"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
