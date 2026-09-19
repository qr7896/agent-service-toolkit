from dataclasses import asdict, dataclass
import hashlib
import json

ACTIONS = {"files", "lexical", "semantic", "structural", "stop"}
SAFE_EXPLORATION_ACTIONS = frozenset({"files", "lexical", "semantic", "structural", "stop"})


@dataclass(frozen=True)
class RewardConfig:
    token_weight: float = 0.001
    call_weight: float = 0.1
    risk_weight: float = 0.5

    def validate(self):
        if min(self.token_weight, self.call_weight, self.risk_weight) < 0:
            raise ValueError("reward weights must be non-negative")
        return self

    def fingerprint(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


FROZEN_REWARD_V1 = RewardConfig()


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
    schema_version: str = "v2-decision-v1"
    reward_config_sha256: str = FROZEN_REWARD_V1.fingerprint()

    def validate(self):
        names = [candidate.action for candidate in self.candidates]
        if not self.task_id or self.step < 0:
            raise ValueError("task_id and non-negative step are required")
        if len(names) != len(set(names)) or not set(names).issubset(SAFE_EXPLORATION_ACTIONS):
            raise ValueError("candidate actions must be unique and safe")
        if self.chosen_action not in names:
            raise ValueError("chosen action must be a candidate")
        if any(not 0 < candidate.propensity <= 1 for candidate in self.candidates):
            raise ValueError("propensities must be in (0, 1]")
        if abs(sum(candidate.propensity for candidate in self.candidates) - 1.0) > 1e-6:
            raise ValueError("candidate propensities must sum to 1")
        if not self.schema_version:
            raise ValueError("schema_version is required")
        return self

    def to_dict(self):
        self.validate()
        return {
            "schema_version": self.schema_version,
            "reward_config_sha256": self.reward_config_sha256,
            "task_id": self.task_id,
            "step": self.step,
            "state": self.state,
            "candidates": [asdict(candidate) for candidate in self.candidates],
            "chosen_action": self.chosen_action,
        }


def uniform_candidates(actions, policy_scores=None):
    names = tuple(dict.fromkeys(actions))
    if not names or not set(names).issubset(SAFE_EXPLORATION_ACTIONS):
        raise ValueError("actions must be non-empty and safe")
    mass = 1.0 / len(names)
    scores = policy_scores or {}
    return tuple(CandidateAction(name, mass, float(scores.get(name, 0.0))) for name in names)


def reward(evidence_gain, tokens, tool_calls, risk, *, token_weight=None, call_weight=None, risk_weight=None, config=None):
    cfg = (config or FROZEN_REWARD_V1).validate()
    tw = cfg.token_weight if token_weight is None else token_weight
    cw = cfg.call_weight if call_weight is None else call_weight
    rw = cfg.risk_weight if risk_weight is None else risk_weight
    return float(evidence_gain) - tw * int(tokens) - cw * int(tool_calls) - rw * float(risk)
