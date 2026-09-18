import argparse
import hashlib
import json
from pathlib import Path

FILES = (
    "evals/v1_decision_dataset.py",
    "evals/v1_train_ranker.py",
    "evals/v1_train_stopper.py",
    "evals/results/v1_decision_episodes.jsonl",
    "evals/results/v1_ranker_metrics.json",
    "evals/results/v1_stopper_metrics.json",
    "evals/results/v1_logreg_ranker.joblib",
    "evals/results/v1_logreg_stopper.joblib",
)


def sha256(path):
    path = Path(path)
    data = path.read_bytes()
    if path.suffix in {".json", ".jsonl", ".py"}:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=Path("evals/results/v1_frozen_manifest.json"))
    args = ap.parse_args()
    rank = json.loads(Path("evals/results/v1_ranker_metrics.json").read_text(encoding="utf-8"))
    stop = json.loads(Path("evals/results/v1_stopper_metrics.json").read_text(encoding="utf-8"))
    manifest = {
        "protocol": "V1 frozen policy before test evaluation",
        "ranker": rank["selected_on_dev"],
        "stopper": "logreg",
        "stop_threshold": stop["threshold"],
        "split_policy": "group-aware cluster-disjoint and source-commit-disjoint; not claimed temporal",
        "test_status": "frozen_not_evaluated",
        "files": {path: sha256(path) for path in FILES},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
