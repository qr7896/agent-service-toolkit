from __future__ import annotations
from collections import Counter
from evals.v2_dataset import validate_records


def distribution_report(records: list[dict], *, min_records: int = 200) -> dict:
    validation = validate_records(records, min_records=min_records)
    splits = Counter()
    clusters = Counter()
    commits = Counter()
    candidate_counts = Counter()
    steps = Counter()
    for row in records:
        state = row.get("state", {})
        splits[state.get("split") or "unknown"] += 1
        clusters[state.get("cluster") or "unknown"] += 1
        commits[state.get("source_commit") or "unknown"] += 1
        steps[int(row.get("step", 0))] += 1
        for candidate in row.get("candidates", []):
            candidate_counts[candidate.get("action", "unknown")] += 1
    return {
        "validation": validation,
        "splits": dict(sorted(splits.items())),
        "clusters": dict(sorted(clusters.items())),
        "source_commits": len([k for k in commits if k != "unknown"]),
        "records_without_commit": commits.get("unknown", 0),
        "candidate_action_counts": dict(sorted(candidate_counts.items())),
        "decision_step_counts": dict(sorted(steps.items())),
    }
