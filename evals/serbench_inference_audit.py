from __future__ import annotations

import argparse
import json
from pathlib import Path


def audit(rows: list[dict]) -> dict:
    stages = {}
    repos = {}
    candidate_counts = []
    observed_counts = []
    errors = []
    for i, row in enumerate(rows):
        sid = str(row.get("state_id", ""))
        if not sid:
            errors.append(f"row {i}: missing state_id")
        candidates = row.get("candidate_evidence", [])
        if not isinstance(candidates, list):
            errors.append(f"{sid}: candidate_evidence not list")
            continue
        ids = [str(e.get("evidence_id", "")) for e in candidates]
        if any(not x for x in ids):
            errors.append(f"{sid}: candidate missing evidence_id")
        if len(ids) != len(set(ids)):
            errors.append(f"{sid}: duplicate candidate evidence_id")
        candidate_counts.append(len(ids))
        observed_counts.append(len(row.get("observed_evidence_ids", [])))
        stage = str(
            row.get("state_type") or row.get("stage") or row.get("state_stage") or "unknown"
        )
        stages[stage] = stages.get(stage, 0) + 1
        repo = str(row.get("repo") or "unknown")
        repos[repo] = repos.get(repo, 0) + 1
    return {
        "protocol": "serbench-inference-audit-v1",
        "states": len(rows),
        "stages": stages,
        "repositories": len([repo for repo in repos if repo != "unknown"]),
        "repository_state_counts": repos,
        "candidate_count": {
            "min": min(candidate_counts) if candidate_counts else 0,
            "max": max(candidate_counts) if candidate_counts else 0,
            "mean": sum(candidate_counts) / len(candidate_counts) if candidate_counts else 0,
        },
        "observed_evidence_mean": sum(observed_counts) / len(observed_counts)
        if observed_counts
        else 0,
        "errors": errors,
        "inference_ready": bool(rows) and not errors,
        "claim_boundary": "Inference-only audit. No certificates/Gold labels are accepted or inspected.",
    }


def main():
    ap = argparse.ArgumentParser()
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path)
    source.add_argument("--split", choices=["example", "cal500", "test500"])
    ap.add_argument("--data-dir", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    if a.split:
        from serbench import load_dataset

        rows = list(load_dataset(a.split, a.data_dir))
    else:
        rows = [
            json.loads(x) for x in a.input.read_text(encoding="utf-8").splitlines() if x.strip()
        ]
    r = audit(rows)
    a.output.write_text(json.dumps(r, indent=2), encoding="utf-8")
    print(json.dumps(r))


if __name__ == "__main__":
    main()
