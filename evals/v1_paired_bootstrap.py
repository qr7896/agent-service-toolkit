import argparse
import json
import random
from pathlib import Path


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v1", type=Path, default=Path("evals/results/v1_frozen_replay.json"))
    ap.add_argument("--v0", type=Path, default=Path("evals/results/v1_matched_v0_utility.json"))
    ap.add_argument("--samples", type=int, default=5000)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--output", type=Path, default=Path("evals/results/v1_paired_bootstrap.json"))
    args = ap.parse_args()
    v1 = json.loads(args.v1.read_text(encoding="utf-8"))
    v0 = json.loads(args.v0.read_text(encoding="utf-8"))
    baseline = v0["utility_gate_groupaware"]
    a = {r["instance_id"]: r for r in v1["rows"]}
    b = {r["instance_id"]: r for r in baseline["rows"]}
    ids = sorted(set(a) & set(b))
    if set(a) != set(b):
        raise RuntimeError("V1/fair V0 task IDs differ")
    metrics = {"context_recall": False, "context_tokens": True, "tool_calls": True}
    paired = {
        m: [(b[i][m] - a[i][m]) if lower else (a[i][m] - b[i][m]) for i in ids]
        for m, lower in metrics.items()
    }
    seed_runs = []
    for seed in args.seeds:
        rng = random.Random(seed)
        boot = {m: [] for m in metrics}
        for _ in range(args.samples):
            sample = [rng.choice(ids) for _ in ids]
            for m, lower in metrics.items():
                vals = [(b[i][m] - a[i][m]) if lower else (a[i][m] - b[i][m]) for i in sample]
                boot[m].append(mean(vals))
        seed_runs.append(
            {
                "seed": seed,
                "metrics": {
                    m: {
                        "ci95": [
                            round(sorted(boot[m])[int(0.025 * (len(boot[m]) - 1))], 6),
                            round(sorted(boot[m])[int(0.975 * (len(boot[m]) - 1))], 6),
                        ],
                        "positive_direction": mean(paired[m]) >= 0,
                    }
                    for m in metrics
                },
            }
        )
    report = {
        "protocol": "paired task bootstrap against V1-train-only group-aware V0 Utility Gate; positive delta favors V1",
        "tasks": ids,
        "n_tasks": len(ids),
        "samples_per_seed": args.samples,
        "resampling_seeds": args.seeds,
        "seed_semantics": "bootstrap RNG seeds over the same frozen tasks; not independent training seeds",
        "prior_coverage": v0.get("prior_coverage"),
        "fallback_count": v0.get("fallback_count"),
        "metrics": {},
        "seed_runs": seed_runs,
    }
    for m in metrics:
        diffs = paired[m]
        report["metrics"][m] = {
            "mean_delta": round(mean(diffs), 6),
            "wins": sum(x > 0 for x in diffs),
            "ties": sum(x == 0 for x in diffs),
            "losses": sum(x < 0 for x in diffs),
            "direction_consistent_all_seeds": all(
                x["metrics"][m]["positive_direction"] for x in seed_runs
            ),
        }
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
