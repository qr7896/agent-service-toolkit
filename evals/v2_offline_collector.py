from evals.v2_decision_schema import DecisionRecord, uniform_candidates


def collect_deterministic_record(task_id, step, state, actions, chosen_action, policy_scores=None):
    """Build one auditable offline decision record without model calls."""
    candidates = uniform_candidates(actions, policy_scores)
    return DecisionRecord(
        task_id=task_id,
        step=step,
        state=dict(state),
        candidates=candidates,
        chosen_action=chosen_action,
    ).validate()
