from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from evals.serbench_adapter import prediction
from evals.serbench_candidate_ranker import ordered_candidates
from evals.v2_feature_contract import EvidenceStateFeatures
from evals.v2_structural_filter_v3 import is_test_path

METHOD_DIRECT = "v2_direct_stop_lexical_v2_4_0"
METHOD_FROZEN = "v2_candidate_compat_v2_4_1"
RETRIEVAL_ACTIONS = {"repo_search", "read_file"}
TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)


def state_features(row: dict) -> EvidenceStateFeatures:
    """Map only inference-visible SERBench fields into the frozen V2 contract."""
    actions = sum(
        item.get("action_type") in RETRIEVAL_ACTIONS for item in row.get("trajectory_prefix", [])
    )
    observed = [item for item in row.get("candidate_evidence", []) if item.get("observed_by_state")]
    paths = {str(item.get("source_path", "")) for item in observed}
    redundancy = 1.0 - len(paths) / len(observed) if observed else 0.0
    return EvidenceStateFeatures(
        step=actions,
        actions_tried=actions,
        evidence_items=len(observed),
        total_cost=0.0,
        total_risk=0.0,
        mean_redundancy=redundancy,
    )


def direct_sufficiency(row: dict) -> bool:
    """Existing V2 runtime rule, ported without using certificates or Gold."""
    return any(
        item.get("observed_by_state")
        and item.get("source_type") == "repo_chunk"
        and not is_test_path(str(item.get("source_path", "")))
        for item in row.get("candidate_evidence", [])
    )


def _diverse_unobserved(row: dict) -> list[dict]:
    """Reuse lexical order, suppress observed evidence, then reduce same-path redundancy."""
    ordered = ordered_candidates(row)
    unseen = [item for item in ordered if not item.get("observed_by_state")]
    candidates = unseen or ordered
    first, repeated, seen_paths = [], [], set()
    for item in candidates:
        path = str(item.get("source_path", ""))
        if path in seen_paths:
            repeated.append(item)
        else:
            seen_paths.add(path)
            first.append(item)
    return first + repeated


def rank_state(row: dict, method: str, k: int = 8) -> dict:
    state_features(row)  # Fail early if the official row cannot map to the V2 contract.
    if method == METHOD_DIRECT and direct_sufficiency(row):
        ranked = []
    elif method == METHOD_DIRECT:
        ranked = ordered_candidates(row)
    elif method == METHOD_FROZEN:
        # SERBench asks for still-missing support. Presence of any observed source file is
        # therefore not a valid STOP condition; observed items are treated as redundant.
        ranked = _diverse_unobserved(row)
    else:
        raise ValueError(f"unknown method: {method}")
    return prediction(
        str(row["state_id"]), method, [str(item["evidence_id"]) for item in ranked[:k]]
    )


def run(rows: list[dict], method: str, k: int) -> tuple[list[dict], dict]:
    predictions = [rank_state(row, method, k) for row in rows]
    by_id = {str(row["state_id"]): row for row in rows}
    proxy_tokens = 0
    observed_suppressed = 0
    for result in predictions:
        row = by_id[str(result["state_id"])]
        candidates = {str(x["evidence_id"]): x for x in row.get("candidate_evidence", [])}
        for evidence_id in result["ranked_evidence_ids"]:
            item = candidates[evidence_id]
            proxy_tokens += len(TOKEN_RE.findall(str(item.get("content_excerpt", ""))))
            observed_suppressed += bool(item.get("observed_by_state"))
    stops = sum(not result["ranked_evidence_ids"] for result in predictions)
    diagnostics = {
        "protocol": "serbench-v2-compatible-v1",
        "method": method,
        "states": len(rows),
        "evidence_items": sum(len(x["ranked_evidence_ids"]) for x in predictions),
        "evidence_proxy_tokens": proxy_tokens,
        "retrieval_action_count": len(rows) - stops,
        "stop_count": stops,
        "stop_rate": stops / len(rows) if rows else 0.0,
        "modality_distribution": dict(
            Counter(
                "stop" if not x["ranked_evidence_ids"] else "supplied_candidate"
                for x in predictions
            )
        ),
        "selected_observed_items": observed_suppressed,
        "features": [
            "step",
            "actions_tried",
            "evidence_items",
            "total_cost",
            "total_risk",
            "mean_redundancy",
        ],
        "unavailable_modalities": ["repository_files", "semantic", "structural_codegraph"],
        "filter_v3": "not_applicable: structural-only repository acquisition filter",
        "claim_boundary": "Supplied-candidate compatibility only; proxy tokens are not provider tokens.",
    }
    return predictions, diagnostics


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["example", "cal500", "test500"], required=True)
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--method", choices=[METHOD_DIRECT, METHOD_FROZEN], required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--diagnostics", type=Path, required=True)
    ap.add_argument("-k", type=int, default=8)
    args = ap.parse_args()
    from serbench import load_dataset

    rows = list(load_dataset(args.split, data_dir=args.data_dir))
    predictions, diagnostics = run(rows, args.method, args.k)
    args.output.write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in predictions),
        encoding="utf-8",
    )
    args.diagnostics.write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    print(json.dumps(diagnostics))


if __name__ == "__main__":
    main()
