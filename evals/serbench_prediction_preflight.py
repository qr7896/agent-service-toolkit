from __future__ import annotations

import argparse
import json
from pathlib import Path


def audit_rows(rows: list[dict], predictions_path: Path) -> dict:
    preds = [
        json.loads(x)
        for x in predictions_path.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]
    pools = {
        str(r["state_id"]): {str(e["evidence_id"]) for e in r.get("candidate_evidence", [])}
        for r in rows
    }
    errors = []
    seen = set()
    ranking_lengths = []
    abstentions = 0
    for p in preds:
        key = (str(p.get("state_id")), str(p.get("method")))
        if key in seen:
            errors.append(f"duplicate state/method: {key}")
        seen.add(key)
        ids = [str(x) for x in p.get("ranked_evidence_ids", [])]
        ranking_lengths.append(len(ids))
        abstentions += not ids
        if len(ids) != len(set(ids)):
            errors.append(f"duplicate evidence ids: {key}")
        if key[0] not in pools:
            errors.append(f"unknown state: {key[0]}")
        elif not set(ids) <= pools[key[0]]:
            errors.append(f"out-of-pool ids: {key}")
    predicted_states = {str(p.get("state_id")) for p in preds}
    missing_states = sorted(set(pools) - predicted_states)
    if missing_states:
        errors.append(f"missing predictions: {len(missing_states)}")
    return {
        "states": len(rows),
        "predictions": len(preds),
        "candidate_count": sum(len(pool) for pool in pools.values()),
        "ranking_length": {
            "min": min(ranking_lengths, default=0),
            "max": max(ranking_lengths, default=0),
            "mean": sum(ranking_lengths) / len(ranking_lengths) if ranking_lengths else 0.0,
        },
        "abstentions": abstentions,
        "inference_failures": len(missing_states),
        "compatibility_failures": len(errors),
        "errors": errors,
        "contract_ready": not errors,
        "claim_boundary": "Local preflight only; upstream SERBench validation/scoring remains authoritative.",
    }


def audit(states_path: Path, predictions_path: Path) -> dict:
    rows = [
        json.loads(x) for x in states_path.read_text(encoding="utf-8").splitlines() if x.strip()
    ]
    return audit_rows(rows, predictions_path)


def main():
    ap = argparse.ArgumentParser()
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--states", type=Path)
    source.add_argument("--split", choices=["example", "cal500"])
    ap.add_argument("--data-dir", type=Path)
    ap.add_argument("--predictions", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    if a.split:
        if a.data_dir is None:
            ap.error("--data-dir is required with --split")
        from serbench import load_dataset

        rows = list(load_dataset(a.split, data_dir=a.data_dir))
        report = audit_rows(rows, a.predictions)
    else:
        report = audit(a.states, a.predictions)
    a.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
