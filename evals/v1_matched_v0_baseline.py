import argparse
import json
import tempfile
from pathlib import Path

from evals.adaptive_retrieval_benchmark import (
    TASKS,
    _merge,
    adaptive,
    backend_outputs,
    preferred_actions,
    score,
    summarize,
)
from evals.swe_tasks import load_tasks, prepare
from evals.v1_decision_dataset import V1_CLUSTER_SPLIT


def split(spec):
    return V1_CLUSTER_SPLIT[spec.cluster]


def evaluate_arm(tasks, cached, budget, preferred_by_cluster, arm):
    rows = []
    fallback_count = 0
    for spec in tasks:
        if arm == "evidence_gate":
            preferred = "lexical"
        else:
            preferred = preferred_by_cluster.get(spec.cluster, "lexical")
            fallback_count += int(spec.cluster not in preferred_by_cluster)
        actions = adaptive(cached[spec.instance_id], preferred)
        run = _merge(cached[spec.instance_id], actions, budget)
        run.instance_id = spec.instance_id
        run.arm = arm
        rows.append(score(run, spec))
    return {"summary": summarize(rows), "rows": rows, "fallback_count": fallback_count}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=8000)
    ap.add_argument("--output", type=Path, default=Path("evals/results/v1_matched_v0_utility.json"))
    args = ap.parse_args()
    all_tasks = load_tasks(TASKS)
    train = [t for t in all_tasks if split(t) == "train"]
    test = [t for t in all_tasks if split(t) == "test"]
    from agents.tools import get_embeddings

    embedding = get_embeddings()
    cached = {}
    with tempfile.TemporaryDirectory(prefix="v1-matched-v0-") as temp:
        base = Path(temp)
        for spec in [*train, *test]:
            root = prepare(spec, base / spec.instance_id)
            cached[spec.instance_id] = backend_outputs(spec, root, embedding)
    priors = preferred_actions(train, cached, args.budget)
    report = {
        "protocol": "matched V0 gates on exact V1 frozen-test tasks; Utility prior fit on V1 train only",
        "split_policy": "V1 group-aware cluster/source-commit disjoint",
        "tasks": len(test),
        "train_tasks_for_prior": len(train),
        "budget": args.budget,
        "prior_map": priors,
        "test_clusters": sorted({t.cluster for t in test}),
        "prior_coverage": sum(t.cluster in priors for t in test) / len(test),
        "evidence_gate": evaluate_arm(test, cached, args.budget, priors, "evidence_gate"),
        "utility_gate_groupaware": evaluate_arm(
            test, cached, args.budget, priors, "utility_gate_groupaware"
        ),
    }
    report["fallback_count"] = report["utility_gate_groupaware"]["fallback_count"]
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "tasks",
                    "train_tasks_for_prior",
                    "prior_map",
                    "test_clusters",
                    "prior_coverage",
                    "fallback_count",
                )
            },
            indent=2,
        )
    )
    print(
        json.dumps(
            {k: report[k]["summary"] for k in ("evidence_gate", "utility_gate_groupaware")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
