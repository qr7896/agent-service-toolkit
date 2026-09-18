import argparse
import json
import tempfile
from pathlib import Path

import joblib

from evals.adaptive_retrieval_benchmark import TASKS, _merge, backend_outputs, gold, summarize
from evals.retrieval_metrics import task_metrics
from evals.swe_tasks import load_tasks, prepare
from evals.v1_decision_dataset import ACTIONS
from evals.v1_evaluate_frozen import verify_manifest
from evals.v1_replay_frozen_policy import learned_actions, split

ABLATIONS = {
    "full": set(),
    "no_structural": {"structural"},
    "no_semantic": {"semantic"},
    "no_lexical": {"lexical"},
    "no_files": {"files"},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=8000)
    ap.add_argument("--output", type=Path, default=Path("evals/results/v1_action_ablation.json"))
    args = ap.parse_args()
    manifest = json.loads(Path("evals/results/v1_frozen_manifest.json").read_text(encoding="utf-8"))
    mismatches = verify_manifest(manifest)
    if mismatches:
        raise RuntimeError(f"Frozen manifest mismatch: {mismatches}")
    ranker = joblib.load("evals/results/v1_logreg_ranker.joblib")
    stopper = joblib.load("evals/results/v1_logreg_stopper.joblib")
    threshold = float(manifest["stop_threshold"])
    tasks = [t for t in load_tasks(TASKS) if split(t) == "test"]
    from agents.tools import get_embeddings

    embedding = get_embeddings()
    rows = {name: [] for name in ABLATIONS}
    with tempfile.TemporaryDirectory(prefix="v1-action-ablation-") as temp:
        base = Path(temp)
        for spec in tasks:
            root = prepare(spec, base / spec.instance_id)
            outputs = backend_outputs(spec, root, embedding)
            for name, removed in ABLATIONS.items():
                allowed = tuple(a for a in ACTIONS if a not in removed)
                actions, decisions = learned_actions(
                    spec, outputs, args.budget, ranker, stopper, threshold, allowed_actions=allowed
                )
                run = _merge(outputs, actions, args.budget)
                run.instance_id = spec.instance_id
                run.arm = name
                rows[name].append(
                    {
                        **run.__dict__,
                        **task_metrics(run.__dict__, gold(spec)),
                        "cluster": spec.cluster,
                        "decisions": decisions,
                    }
                )
    report = {
        "protocol": "frozen V1 action-space ablation; frozen models unchanged",
        "manifest_verified": True,
        "tasks": len(tasks),
        "budget": args.budget,
        "ablations": {
            name: {"removed_actions": sorted(ABLATIONS[name]), "summary": summarize(rs), "rows": rs}
            for name, rs in rows.items()
        },
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({name: v["summary"] for name, v in report["ablations"].items()}, indent=2))


if __name__ == "__main__":
    main()
