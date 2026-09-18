from dataclasses import dataclass

from evals.evidence_runtime import ACTION_COST, ACTION_RISK


@dataclass(frozen=True)
class EvidenceBudget:
    max_actions: int = 4
    max_cost: float = 4.0
    max_risk: float = 1.0


class EvidencePolicy:
    version = "runtime-v0"

    def __init__(self, budget=None):
        self.budget = budget or EvidenceBudget()

    def remaining(self, ledger):
        summary = ledger.summary()
        return {
            "actions": max(0, self.budget.max_actions - summary["action_count"]),
            "cost": max(0.0, self.budget.max_cost - summary["total_cost"]),
            "risk": max(0.0, self.budget.max_risk - summary["total_risk"]),
        }

    def allowed(self, ledger, action):
        if action not in ACTION_COST:
            return False
        remaining = self.remaining(ledger)
        return (
            remaining["actions"] >= 1
            and remaining["cost"] >= ACTION_COST[action]
            and remaining["risk"] >= ACTION_RISK[action]
        )

    def choose(self, ledger, candidates, utility=None):
        utility = utility or {}
        allowed = [a for a in candidates if self.allowed(ledger, a)]
        if not allowed:
            return "stop"
        best = max(allowed, key=lambda a: (self.score(ledger, a, utility), -ACTION_COST[a], a))
        return best if self.score(ledger, best, utility) > 0 else "stop"

    def score(self, ledger, action, utility):
        return utility.get(action, 0.0) - 0.1 * ACTION_COST[action] - 0.1 * ACTION_RISK[action]

    def state(self, ledger):
        summary = ledger.summary()
        return {
            "policy_version": self.version,
            "remaining": self.remaining(ledger),
            "spent": {
                "actions": summary["action_count"],
                "cost": summary["total_cost"],
                "risk": summary["total_risk"],
            },
            "unique_evidence": summary["unique_evidence"],
            "mean_redundancy": summary["mean_redundancy"],
        }


class RuntimeEvidencePolicyV1(EvidencePolicy):
    version = "runtime-v1"

    def __init__(self, budget=None, redundancy_weight=0.3, depth_weight=0.05):
        super().__init__(budget)
        self.redundancy_weight = redundancy_weight
        self.depth_weight = depth_weight

    def score(self, ledger, action, utility):
        score = super().score(ledger, action, utility)
        previous = [row["redundancy"] for row in ledger.actions if row["action"] == action]
        if previous:
            score -= self.redundancy_weight * previous[-1]
        if action == "structural":
            depths = [
                item.depth
                for item in ledger.items
                if item.source == "structural" and item.depth is not None
            ]
            if depths:
                score -= self.depth_weight * max(depths)
        return score
