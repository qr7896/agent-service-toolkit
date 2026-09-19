from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def classify(off: dict[str, Any], on: dict[str, Any]) -> str:
    if on["success"] and not off["success"]:
        return "helpful_memory"
    if off["success"] and not on["success"]:
        return "harmful_memory"
    if off.get("patch_sha256") and off.get("patch_sha256") == on.get("patch_sha256"):
        return "redundant_memory"
    return "behavior_changed_no_success_delta"


def summarize(paths: list[Path]) -> dict[str, Any]:
    pairs = []
    counts = {
        "helpful_memory": 0,
        "harmful_memory": 0,
        "redundant_memory": 0,
        "behavior_changed_no_success_delta": 0,
    }
    for path in paths:
        row = json.loads(path.read_text(encoding="utf-8"))
        off, on = row["results"]
        kind = row.get("outcome_class") or classify(off, on)
        counts[kind] += 1
        pairs.append(
            {
                "path": str(path),
                "outcome_class": kind,
                "success_delta": int(on["success"]) - int(off["success"]),
                "token_delta": on["provider_usage"]["total_tokens"]
                - off["provider_usage"]["total_tokens"],
                "wall_time_delta_ms": round(on["wall_time_ms"] - off["wall_time_ms"], 1),
                "same_patch": off.get("patch_sha256") == on.get("patch_sha256")
                if off.get("patch_sha256")
                else None,
            }
        )
    return {
        "protocol": "v3-paired-memory-report-v1",
        "pairs": pairs,
        "counts": counts,
        "n": len(pairs),
        "claim_boundary": "Descriptive paired evidence only; do not infer causal efficacy from a small exploratory sample.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("comparisons", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.comparisons)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
