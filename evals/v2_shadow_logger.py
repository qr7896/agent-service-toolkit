from evals.v2_decision_schema import DecisionRecord, uniform_candidates


class V2ShadowDecisionLogger:
    """Observe EvidenceController choices without changing the policy decision."""

    def __init__(self, task_id, writer, context=None):
        self.task_id = task_id
        self.writer = writer
        self.context = dict(context or {})
        self.step = 0

    def record(self, *, before, candidates, chosen_action, utility):
        safe_candidates = list(dict.fromkeys([*candidates, "stop"]))
        scores = dict(utility or {})
        scores.setdefault("stop", 0.0)
        state = {**self.context, "policy_state": before}
        record = DecisionRecord(
            task_id=self.task_id,
            step=self.step,
            state=state,
            candidates=uniform_candidates(safe_candidates, scores),
            chosen_action=chosen_action,
        ).validate()
        self.writer.append(record)
        self.step += 1
        return record
