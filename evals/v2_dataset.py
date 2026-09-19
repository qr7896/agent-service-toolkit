from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from evals.v2_decision_schema import SAFE_EXPLORATION_ACTIONS

FORBIDDEN_RUNTIME_KEYS = {
    "gold",
    "gold_files",
    "gold_symbols",
    "oracle_gain",
    "oracle_value",
    "oracle_best_action",
    "stop_label",
    "context_recall_after",
}
REQUIRED_KEYS = {
    "schema_version",
    "reward_config_sha256",
    "task_id",
    "step",
    "state",
    "candidates",
    "chosen_action",
}


def canonical_record_sha256(record: dict) -> str:
    payload = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def validate_records(records: list[dict], *, min_records: int = 200) -> dict:
    errors = []
    hashes = []
    task_steps = set()
    action_counts = Counter()
    task_groups = defaultdict(set)
    commit_groups = defaultdict(set)

    for index, row in enumerate(records):
        missing = REQUIRED_KEYS - set(row)
        if missing:
            errors.append(f"row {index}: missing {sorted(missing)}")
            continue
        leaked = sorted(set(_walk_keys(row.get("state", {}))) & FORBIDDEN_RUNTIME_KEYS)
        if leaked:
            errors.append(f"row {index}: runtime leakage {leaked}")
        candidates = row.get("candidates") or []
        actions = [candidate.get("action") for candidate in candidates]
        if not actions or not set(actions).issubset(SAFE_EXPLORATION_ACTIONS):
            errors.append(f"row {index}: unsafe/empty candidates")
        if row["chosen_action"] not in actions:
            errors.append(f"row {index}: chosen action not candidate")
        mass = sum(float(candidate.get("propensity", 0)) for candidate in candidates)
        if abs(mass - 1.0) > 1e-6:
            errors.append(f"row {index}: propensity mass {mass}")
        key = (row["task_id"], int(row["step"]))
        if key in task_steps:
            errors.append(f"row {index}: duplicate task-step {key}")
        task_steps.add(key)
        hashes.append(canonical_record_sha256(row))
        action_counts[row["chosen_action"]] += 1
        split = row.get("state", {}).get("split")
        cluster = row.get("state", {}).get("cluster")
        commit = row.get("state", {}).get("source_commit")
        if cluster and split:
            task_groups[cluster].add(split)
        if commit and split:
            commit_groups[commit].add(split)

    duplicate_hashes = len(hashes) - len(set(hashes))
    cross_clusters = sorted(key for key, values in task_groups.items() if len(values) > 1)
    cross_commits = sorted(key for key, values in commit_groups.items() if len(values) > 1)
    if duplicate_hashes:
        errors.append(f"duplicate record hashes: {duplicate_hashes}")
    if cross_clusters:
        errors.append(f"cross-split clusters: {cross_clusters}")
    if cross_commits:
        errors.append(f"cross-split commits: {cross_commits}")

    return {
        "records": len(records),
        "tasks": len({row.get("task_id") for row in records}),
        "ready_for_replay": len(records) >= min_records and not errors,
        "minimum_records": min_records,
        "duplicate_hashes": duplicate_hashes,
        "cross_split_clusters": cross_clusters,
        "cross_split_commits": cross_commits,
        "chosen_action_counts": dict(sorted(action_counts.items())),
        "errors": errors,
    }


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
