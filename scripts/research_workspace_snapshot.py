"""Create a non-destructive inventory of the research worktree.

This script never deletes, moves, stages, commits, or rewrites existing files.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research_workspace_snapshot_2026-09-26.json"


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify(path: str) -> str:
    normalized = path.replace("\\\\", "/")
    name = Path(normalized).name.lower()
    if (
        "strict_v7" in name
        or "strict-v7" in name
        or normalized.endswith("E1C_STRICT_BLIND_DEV30_TO_FRESH30_PLAYBOOK.md")
    ):
        return "current_lineage"
    if normalized.startswith((".codex/", ".pytest_cache/", "__pycache__/")):
        return "cache_or_runtime"
    if normalized.startswith("evals/results/"):
        return "generated_evidence"
    if normalized.startswith("data/") and (
        name.endswith(".json")
        or name.endswith(".jsonl")
        or name.endswith(".csv")
    ):
        return "generated_evidence"
    if normalized.startswith(("docs/research/", "evals/", "tests/")):
        return "historical_research"
    if normalized.startswith("docs/") and "PROGRESS_RESEARCH_ROADMAP" in normalized:
        return "historical_research"
    if normalized.startswith("scripts/") and (
        "experiment_" in name or "wave_b_" in name or "research_workspace_" in name
    ):
        return "historical_research"
    if normalized == "src/agents/model_budget.py":
        return "historical_research"
    return "unknown"


def build() -> dict:
    porcelain = _git("status", "--porcelain=v1", "--untracked-files=all").splitlines()
    rows = []
    for line in porcelain:
        status = line[:2]
        raw_path = line[3:]
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ", 1)[1]
        path = raw_path.strip('"')
        absolute = ROOT / path
        rows.append(
            {
                "status": status,
                "path": path.replace("\\\\", "/"),
                "classification": classify(path),
                "exists": absolute.exists(),
                "is_file": absolute.is_file(),
                "size_bytes": absolute.stat().st_size if absolute.is_file() else None,
                "sha256": _sha256(absolute),
            }
        )
    counts = Counter(row["classification"] for row in rows)
    value = {
        "schema": "webcodex-research-workspace-snapshot-v1",
        "head": _git("rev-parse", "HEAD").strip(),
        "branch": _git("branch", "--show-current").strip(),
        "dirty": bool(rows),
        "changed_path_count": len(rows),
        "classification_counts": dict(sorted(counts.items())),
        "destructive_cleanup_performed": False,
        "files_moved": 0,
        "files_deleted": 0,
        "files_staged": 0,
        "files_committed": 0,
        "policy": {
            "current_lineage": "KEEP",
            "historical_research": "KEEP_UNLESS_EXPLICITLY_ARCHIVED",
            "generated_evidence": "KEEP_AS_RESEARCH_EVIDENCE",
            "cache_or_runtime": "REVIEW_SEPARATELY_BEFORE_CLEANUP",
            "unknown": "MANUAL_REVIEW_REQUIRED",
        },
        "rows": rows,
    }
    value["snapshot_sha256"] = hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value


def main() -> None:
    value = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                key: value[key]
                for key in (
                    "head",
                    "branch",
                    "changed_path_count",
                    "classification_counts",
                    "destructive_cleanup_performed",
                    "snapshot_sha256",
                )
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
