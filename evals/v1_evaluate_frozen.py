import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, average_precision_score, brier_score_loss, roc_auc_score

from evals.v1_train_ranker import evaluate as evaluate_ranker
from evals.v1_train_ranker import load_rows as load_ranker_rows
from evals.v1_train_stopper import ece
from evals.v1_train_stopper import load_rows as load_stopper_rows


def sha256(path):
    path = Path(path)
    data = path.read_bytes()
    if path.suffix in {".json", ".jsonl", ".py"}:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def verify_manifest(manifest):
    mismatches = []
    for path, expected in manifest["files"].items():
        actual = sha256(path)
        if actual != expected:
            mismatches.append({"path": path, "expected": expected, "actual": actual})
    return mismatches


def evaluate_stopper(model, rows, threshold):
    x = np.asarray([r["x"] for r in rows])
    y = np.asarray([r["y"] for r in rows])
    p = model.predict_proba(x)[:, 1]
    pred = p >= threshold
    out = {
        "episodes": len(rows),
        "stop_rate": round(float(y.mean()), 6),
        "accuracy": round(float(accuracy_score(y, pred)), 6),
        "false_stop": int(((pred == 1) & (y == 0)).sum()),
        "missed_stop": int(((pred == 0) & (y == 1)).sum()),
        "auprc": round(float(average_precision_score(y, p)), 6),
        "brier": round(float(brier_score_loss(y, p)), 6),
        "ece_5bin": round(ece(y, p), 6),
    }
    out["auroc"] = round(float(roc_auc_score(y, p)), 6) if len(set(y)) > 1 else None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=Path("evals/results/v1_frozen_manifest.json"))
    ap.add_argument(
        "--output", type=Path, default=Path("evals/results/v1_frozen_test_metrics.json")
    )
    args = ap.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    mismatches = verify_manifest(manifest)
    if mismatches:
        raise RuntimeError(f"Frozen manifest mismatch: {mismatches}")
    rank_model = joblib.load("evals/results/v1_logreg_ranker.joblib")
    stop_model = joblib.load("evals/results/v1_logreg_stopper.joblib")
    rank_test = [
        r
        for r in load_ranker_rows("evals/results/v1_decision_episodes.jsonl")
        if r["split"] == "test"
    ]
    stop_test = [
        r
        for r in load_stopper_rows("evals/results/v1_decision_episodes.jsonl")
        if r["split"] == "test"
    ]
    report = {
        "protocol": "one-shot frozen V1 test evaluation",
        "manifest_verified": True,
        "ranker": evaluate_ranker(rank_model, rank_test),
        "stopper": evaluate_stopper(stop_model, stop_test, float(manifest["stop_threshold"])),
    }
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
