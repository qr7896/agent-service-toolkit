from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def write_predictions(
    rows: list[dict], output: Path, method: str = "v2_integration_abstain"
) -> None:
    # Empty ranking is a valid SERBench abstention. This runner deliberately does
    # not invent a ranking algorithm just to pass the integration gate.
    with output.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(
                json.dumps(
                    {"state_id": row["state_id"], "method": method, "ranked_evidence_ids": []},
                    ensure_ascii=False,
                )
                + "\n"
            )


def run_upstream(serbench_root: Path, split: str, output: Path, method: str) -> int:
    # Reuse upstream loader by importing from its checkout; never read certificates here.
    sys.path.insert(0, str(serbench_root / "src"))
    from serbench import load_dataset  # type: ignore

    rows = list(load_dataset(split))
    write_predictions(rows, output, method)
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serbench-root", type=Path, required=True)
    ap.add_argument("--split", choices=["example", "cal500"], default="example")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--method", default="v2_integration_abstain")
    a = ap.parse_args()
    n = run_upstream(a.serbench_root, a.split, a.output, a.method)
    print(
        json.dumps(
            {
                "split": a.split,
                "states": n,
                "prediction_file": str(a.output),
                "next": "score with upstream SERBench CLI/API",
            }
        )
    )


if __name__ == "__main__":
    main()
