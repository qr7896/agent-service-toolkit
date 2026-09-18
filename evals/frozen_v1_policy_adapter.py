import json
from pathlib import Path

import joblib
import numpy as np

from evals.adaptive_retrieval_benchmark import BACKEND_COST
from evals.evidence_policy import EvidencePolicy
from evals.v1_decision_dataset import ACTION_RISK
from evals.v1_evaluate_frozen import verify_manifest
from evals.v1_train_ranker import PRE_ACTION_FEATURES, _vector
from evals.v1_train_stopper import vector as stopper_vector


class FrozenV1PolicyAdapter(EvidencePolicy):
    version = "frozen-v1-adapter"

    def __init__(
        self,
        task_text,
        budget=None,
        manifest_path=Path("evals/results/v1_frozen_manifest.json"),
        ranker_path=Path("evals/results/v1_logreg_ranker.joblib"),
        stopper_path=Path("evals/results/v1_logreg_stopper.joblib"),
    ):
        super().__init__(budget)
        self.task_text = task_text
        self.manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        mismatches = verify_manifest(self.manifest)
        if mismatches:
            raise RuntimeError(f"Frozen manifest mismatch: {mismatches}")
        self.ranker = joblib.load(ranker_path)
        self.stopper = joblib.load(stopper_path)
        self.threshold = float(self.manifest["stop_threshold"])
        self.last_decision = None

    def _candidate(self, ledger, action):
        paths = {item.path for item in ledger.items}
        symbols = {item.symbol for item in ledger.items if item.symbol}
        features = {
            "round": len(ledger.actions),
            "actions_tried": len(ledger.actions),
            "tokens_spent": sum(
                max(1, len(item.content) // 4) for item in ledger.items if item.content
            ),
            "cost_spent": ledger.summary()["total_cost"],
            "artifact_files": len(paths),
            "artifact_symbols": len(symbols),
            "artifact_tests": len({path for path in paths if "test" in Path(path).name.lower()}),
            "artifact_callers": len(
                {item.key for item in ledger.items if item.relation_type == "caller"}
            ),
            "candidate_cost": BACKEND_COST[action],
            "candidate_risk": ACTION_RISK[action],
        }
        return {"action": action, "features": features}

    def choose(self, ledger, candidates, utility=None):
        allowed = [action for action in candidates if self.allowed(ledger, action)]
        if not allowed:
            self.last_decision = {"decision": "stop", "reason": "budget_or_capability"}
            return "stop"
        rows = [self._candidate(ledger, action) for action in allowed]
        episode = {"candidates": [rows[0]], "task_text": self.task_text}
        stop_probability = float(
            self.stopper.predict_proba(np.asarray([stopper_vector(episode)]))[0, 1]
        )
        if stop_probability >= self.threshold:
            self.last_decision = {
                "decision": "stop",
                "stop_probability": round(stop_probability, 6),
                "threshold": self.threshold,
            }
            return "stop"
        scores = self.ranker.predict_proba(
            np.asarray([_vector(row, self.task_text, PRE_ACTION_FEATURES, True) for row in rows])
        )[:, 1]
        chosen = allowed[int(np.argmax(scores))]
        self.last_decision = {
            "decision": chosen,
            "stop_probability": round(stop_probability, 6),
            "threshold": self.threshold,
            "rank_scores": {
                action: round(float(score), 6) for action, score in zip(allowed, scores)
            },
        }
        return chosen

    def state(self, ledger):
        state = super().state(ledger)
        state["frozen_v1"] = {
            "manifest_verified": True,
            "last_decision": self.last_decision,
        }
        return state
