from dataclasses import dataclass

ACTIONS = {"files", "lexical", "semantic", "structural", "stop"}


@dataclass(frozen=True)
class CandidateAction:
    action: str
    propensity: float
    policy_score: float


@dataclass(frozen=True)
class DecisionRecord:
    task_id: str
    step: int
    state: dict
    candidates: tuple[CandidateAction, ...]
    chosen_action: str

    def validate(self):
        names = [candidate.action for candidate in self.candidates]
        if not self.task_id or self.step < 0:
            raise ValueError("task_id and non-negative step are required")
        if len(names) != len(set(names)) or not set(names).issubset(ACTIONS):
            raise ValueError("candidate actions must be unique and known")
        if self.chosen_action not in names:
            raise ValueError("chosen action must be a candidate")
        if any(not 0 < candidate.propensity <= 1 for candidate in self.candidates):
            raise ValueError("propensities must be in (0, 1]")
        if abs(sum(candidate.propensity for candidate in self.candidates) - 1.0) > 1e-6:
            raise ValueError("candidate propensities must sum to 1")
        return self


def reward(evidence_gain, tokens, tool_calls, risk, *, token_weight, call_weight, risk_weight):
    return (
        float(evidence_gain)
        - token_weight * int(tokens)
        - call_weight * int(tool_calls)
        - risk_weight * float(risk)
    )
