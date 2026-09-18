import argparse
import json
import statistics
from pathlib import Path


def pct(delta, base):
    return None if not base else round(delta / base * 100.0, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v1", type=Path, default=Path("evals/results/v1_frozen_replay.json"))
    ap.add_argument("--v0", type=Path, default=Path("evals/results/v1_matched_v0_utility.json"))
    ap.add_argument("--output", type=Path, default=Path("evals/results/v1_go_no_go.json"))
    args = ap.parse_args()
    v1 = json.loads(args.v1.read_text(encoding="utf-8"))
    v0 = json.loads(args.v0.read_text(encoding="utf-8"))
    learned = v1["summary"]
    baseline_block = v0["utility_gate_groupaware"]
    baseline = baseline_block["summary"]
    a = {r["instance_id"]: r for r in v1["rows"]}
    b = {r["instance_id"]: r for r in baseline_block["rows"]}
    if set(a) != set(b):
        raise RuntimeError("V1/fair V0 task IDs differ")
    ids = sorted(a)

    def med(rows, key):
        return statistics.median(rows[i][key] for i in ids)

    recall_delta = round((learned["context_recall"] or 0) - (baseline["context_recall"] or 0), 4)
    mean_token_reduction = pct(
        (baseline["context_tokens"] or 0) - (learned["context_tokens"] or 0),
        baseline["context_tokens"],
    )
    mean_call_reduction = pct(
        (baseline["avg_tool_calls"] or 0) - (learned["avg_tool_calls"] or 0),
        baseline["avg_tool_calls"],
    )
    v1_med_tokens, base_med_tokens = med(a, "context_tokens"), med(b, "context_tokens")
    v1_med_calls, base_med_calls = med(a, "tool_calls"), med(b, "tool_calls")
    median_token_reduction = pct(base_med_tokens - v1_med_tokens, base_med_tokens)
    median_call_reduction = pct(base_med_calls - v1_med_calls, base_med_calls)
    criterion_recall = recall_delta >= 0
    criterion_cost = (median_token_reduction is not None and median_token_reduction >= 10) or (
        median_call_reduction is not None and median_call_reduction >= 10
    )
    report = {
        "comparison_scope": "paired exact-task comparison against V1-train-only group-aware V0 Utility Gate",
        "task_ids": ids,
        "v1_frozen": learned,
        "v0_utility_gate_groupaware": baseline,
        "prior_coverage": v0.get("prior_coverage"),
        "fallback_count": v0.get("fallback_count"),
        "delta": {
            "context_recall": recall_delta,
            "mean_context_token_reduction_pct": mean_token_reduction,
            "mean_tool_call_reduction_pct": mean_call_reduction,
            "median_context_tokens": {
                "v1": v1_med_tokens,
                "v0": base_med_tokens,
                "reduction_pct": median_token_reduction,
            },
            "median_tool_calls": {
                "v1": v1_med_calls,
                "v0": base_med_calls,
                "reduction_pct": median_call_reduction,
            },
        },
        "go_no_go": {
            "recall_not_below_v0": criterion_recall,
            "median_cost_reduction_at_least_10pct": criterion_cost,
            "multi_seed_consistency": "not_yet_evaluated",
            "provisional_go": bool(criterion_recall and criterion_cost),
            "final_go": False,
            "reason": "final Go additionally requires >=3 paired resampling seeds with consistent direction",
        },
    }
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
