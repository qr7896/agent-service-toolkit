import argparse
import json
import tempfile
from pathlib import Path

import joblib
import numpy as np

from evals.adaptive_retrieval_benchmark import (
    BACKEND_COST,
    TASKS,
    _merge,
    backend_outputs,
    gold,
    summarize,
)
from evals.retrieval_metrics import task_metrics
from evals.swe_tasks import load_tasks, prepare
from evals.v1_decision_dataset import ACTION_RISK, ACTIONS, V1_CLUSTER_SPLIT
from evals.v1_evaluate_frozen import verify_manifest
from evals.v1_train_ranker import PRE_ACTION_FEATURES, _vector
from evals.v1_train_stopper import vector as stopper_vector


def split(spec):
    return V1_CLUSTER_SPLIT[spec.cluster]


def candidate(action, current, decision, tried):
    artifacts = {k: set() for k in ("files", "symbols", "tests", "callers")}
    for step in current.retrieval_trace:
        for key in artifacts:
            artifacts[key].update((step.get("artifacts") or {}).get(key) or [])
    counts = {k: len(v) for k, v in artifacts.items()}
    features = {
        "round": decision,
        "actions_tried": len(tried),
        "tokens_spent": current.estimated_tokens,
        "cost_spent": current.cost,
        "artifact_files": counts["files"],
        "artifact_symbols": counts["symbols"],
        "artifact_tests": counts["tests"],
        "artifact_callers": counts["callers"],
        "candidate_cost": BACKEND_COST[action],
        "candidate_risk": ACTION_RISK[action],
    }
    return {"action": action, "features": features}


def learned_actions(spec, outputs, budget, ranker, stopper, threshold, allowed_actions=None):
    action_space = tuple(a for a in (allowed_actions or ACTIONS) if a in outputs)
    tried = []
    decisions = []
    while len(tried) < len(action_space):
        current = _merge(outputs, tried, budget)
        stop_prob = float(
            stopper.predict_proba(
                np.asarray(
                    [
                        stopper_vector(
                            {
                                "candidates": [candidate("files", current, len(tried), tried)],
                                "task_text": spec.problem_statement,
                                "instance_id": spec.instance_id,
                            }
                        )
                    ]
                )
            )[0, 1]
        )
        if stop_prob >= threshold:
            decisions.append(
                {"round": len(tried), "stop_probability": round(stop_prob, 6), "decision": "stop"}
            )
            break
        available = [a for a in action_space if a not in tried]
        rows = [candidate(a, current, len(tried), tried) for a in available]
        scores = ranker.predict_proba(
            np.asarray(
                [_vector(c, spec.problem_statement, PRE_ACTION_FEATURES, True) for c in rows]
            )
        )[:, 1]
        action = available[int(np.argmax(scores))]
        decisions.append(
            {
                "round": len(tried),
                "stop_probability": round(stop_prob, 6),
                "decision": action,
                "rank_scores": {a: round(float(v), 6) for a, v in zip(available, scores)},
            }
        )
        tried.append(action)
    return tried, decisions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=8000)
    ap.add_argument("--output", type=Path, default=Path("evals/results/v1_frozen_replay.json"))
    args = ap.parse_args()
    manifest = json.loads(Path("evals/results/v1_frozen_manifest.json").read_text(encoding="utf-8"))
    mismatches = verify_manifest(manifest)
    if mismatches:
        raise RuntimeError(f"Frozen manifest mismatch: {mismatches}")
    ranker = joblib.load("evals/results/v1_logreg_ranker.joblib")
    stopper = joblib.load("evals/results/v1_logreg_stopper.joblib")
    threshold = float(manifest["stop_threshold"])
    tasks = [t for t in load_tasks(TASKS) if split(t) == "test"]
    rows = []
    traces = {}
    from agents.tools import get_embeddings

    embedding = get_embeddings()
    with tempfile.TemporaryDirectory(prefix="retrieval-v1-replay-") as temp:
        base = Path(temp)
        for spec in tasks:
            root = prepare(spec, base / spec.instance_id)
            outputs = backend_outputs(spec, root, embedding)
            actions, decisions = learned_actions(
                spec, outputs, args.budget, ranker, stopper, threshold
            )
            run = _merge(outputs, actions, args.budget)
            run.instance_id = spec.instance_id
            run.arm = "V1_frozen"
            rows.append(
                {
                    **run.__dict__,
                    **task_metrics(run.__dict__, gold(spec)),
                    "task_type": spec.task_type,
                    "cluster": spec.cluster,
                }
            )
            traces[spec.instance_id] = decisions
    report = {
        "protocol": "frozen V1 sequential policy replay",
        "manifest_verified": True,
        "budget": args.budget,
        "threshold": threshold,
        "tasks": len(tasks),
        "summary": summarize(rows),
        "decision_traces": traces,
        "rows": rows,
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {"protocol": report["protocol"], "tasks": len(tasks), "summary": report["summary"]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
