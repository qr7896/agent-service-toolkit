from __future__ import annotations

import argparse
import json
from pathlib import Path

from evals.serbench_adapter import prediction


def ordered_candidates(row: dict) -> list[dict]:
    """Deterministic, no-model candidate-pool baseline for integration/calibration.

    Uses only inference-visible issue/information_need/state text and candidate excerpts.
    It is intentionally simple: the purpose is to exercise the official candidate-ranking
    track without inventing a new retriever.
    """
    query = " ".join(
        str(row.get(x, ""))
        for x in (
            "issue",
            "information_need",
            "current_observation",
            "current_hypothesis",
            "current_subgoal",
        )
    ).lower()
    terms = {t for t in query.replace("/", " ").replace("_", " ").split() if len(t) >= 3}
    scored = []
    for i, e in enumerate(row.get("candidate_evidence", [])):
        text = (" ".join(str(e.get(x, "")) for x in ("content_excerpt", "source_path"))).lower()
        score = sum(1 for t in terms if t in text)
        scored.append((-score, i, str(e["evidence_id"])))
    scored.sort()
    candidates = row.get("candidate_evidence", [])
    return [candidates[x[1]] for x in scored]


def rank_state(row: dict, method: str = "v2_candidate_lexical_v1", k: int = 8) -> dict:
    ordered = ordered_candidates(row)
    return prediction(str(row["state_id"]), method, [str(x["evidence_id"]) for x in ordered[:k]])


def rank_rows(rows: list[dict], method: str, k: int) -> list[dict]:
    return [rank_state(r, method, k) for r in rows]


def main():
    ap = argparse.ArgumentParser()
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path)
    source.add_argument("--split", choices=["example", "cal500"])
    ap.add_argument("--data-dir", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--method", default="v2_candidate_lexical_v1")
    ap.add_argument("-k", type=int, default=8)
    a = ap.parse_args()
    if a.split:
        from serbench import load_dataset

        rows = list(load_dataset(a.split, a.data_dir))
    else:
        rows = [
            json.loads(x) for x in a.input.read_text(encoding="utf-8").splitlines() if x.strip()
        ]
    out = rank_rows(rows, a.method, a.k)
    a.output.write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out), encoding="utf-8"
    )
    print(json.dumps({"states": len(out), "method": a.method, "k": a.k}))


if __name__ == "__main__":
    main()
