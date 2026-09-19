from __future__ import annotations

import argparse
import json
from pathlib import Path


def rows(path: Path) -> dict[str, dict]:
    return {
        item["state_id"]: item
        for item in (
            json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line
        )
    }


def build(lexical_path: Path, compat_path: Path, direct_diagnostics: Path) -> dict:
    lexical = rows(lexical_path)
    compat = rows(compat_path)
    direct = json.loads(direct_diagnostics.read_text(encoding="utf-8"))
    ids = sorted(set(lexical) & set(compat))
    return {
        "protocol": "serbench-v2-failure-taxonomy-v1",
        "states": len(ids),
        "failure_modes": {
            "state_representation_mismatch": {
                "count": len(ids),
                "evidence": "SERBench has no V2-compatible cost/risk values; both remain 0.",
            },
            "candidate_only_vs_repository_retrieval_mismatch": {
                "count": len(ids),
                "evidence": "CodeGraph, semantic, and repository file acquisition are unavailable in the core supplied-candidate track.",
            },
            "stop_calibration_failure": {
                "count": direct["stop_count"],
                "evidence": "Direct V2 sufficiency port abstained whenever an observed non-test source chunk existed.",
            },
            "evidence_ranking_failure_at_8": {
                "count": sum(not compat[x]["mss_complete@8"] for x in ids),
                "evidence": "Official per-state mss_complete@8 for the frozen compatible method.",
            },
            "correction_gained_complete_sets": {
                "count": sum(
                    not lexical[x]["mss_complete@8"] and compat[x]["mss_complete@8"] for x in ids
                ),
                "evidence": "Paired Cal500 comparison against deterministic lexical.",
            },
            "correction_lost_complete_sets": {
                "count": sum(
                    lexical[x]["mss_complete@8"] and not compat[x]["mss_complete@8"] for x in ids
                ),
                "evidence": "Path diversity can displace multiple necessary chunks from one source file.",
            },
            "candidate_budget_mismatch": {
                "count": 0,
                "evidence": "All compared ranking methods use the official k=8 budget.",
            },
        },
        "decision": "Freeze after one reasoned correction; no further Cal500 tuning.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lexical", type=Path, required=True)
    ap.add_argument("--compat", type=Path, required=True)
    ap.add_argument("--direct-diagnostics", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = build(args.lexical, args.compat, args.direct_diagnostics)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
