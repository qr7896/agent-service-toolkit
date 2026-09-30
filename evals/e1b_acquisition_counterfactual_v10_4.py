
from evals.e1b_acquisition_policy_interface_v10_4 import (
    DeterministicBaselinePolicy,
    PolicyContext,
    sha256,
)
from evals.e1b_evidence_acquisition_v10_3 import ACTIONS, MAX_ACQUISITION_COST
from evals.e1b_semantic_evidence_ir_v10 import verify
from evals.e1b_verification_decision_v10_1 import decide

SCHEMA_VERSION = "e1b-acquisition-counterfactual-replay-v1"
MAX_REPLAY_STEPS = 8


def replay_arm(obligations, action_results, first_action):
    evidence = []
    attempted = []
    cost = 0
    trace = []
    forced = first_action
    for step in range(MAX_REPLAY_STEPS):
        verification = verify(obligations, evidence)
        decision = decide(obligations, verification, 0)
        if decision["action"] in {"BLOCK_PATCH", "ALLOW_VERIFICATION"}:
            terminal = decision["action"]
            break
        available = [
            action for action in ACTIONS
            if action.name not in attempted
            and any(ob.kind in action.capabilities for ob in obligations)
        ]
        action = next((row for row in available if row.name == forced), None) if forced else None
        forced = None
        if action is None:
            selection = DeterministicBaselinePolicy().select(
                obligations, verification, PolicyContext(tuple(attempted), cost)
            )
            if selection["action"] in {"BYPASS_BLOCK", "EXHAUSTED", "BUDGET_EXHAUSTED"}:
                terminal = "BLOCK_PATCH"
                break
            action = next((row for row in available if row.name == selection["action"]), None)
        if action is None or cost + action.cost > MAX_ACQUISITION_COST:
            terminal = "BLOCK_PATCH"
            break
        attempted.append(action.name)
        cost += action.cost
        evidence.extend(tuple(action_results.get(action.name, ())))
        trace.append({"step": step, "action": action.name, "cost": action.cost, "cumulative_cost": cost})
    else:
        terminal = "BLOCK_PATCH"
    return {
        "first_action": first_action,
        "terminal_action": terminal,
        "steps": len(trace),
        "protocol_cost": cost,
        "evidence_count": len(evidence),
        "trace_sha256": sha256(trace),
    }


def counterfactual_replay(obligations, action_results):
    admissible = [
        action for action in ACTIONS
        if any(ob.kind in action.capabilities for ob in obligations)
    ]
    arms = [replay_arm(obligations, action_results, action.name) for action in admissible]
    result = {
        "schema_version": SCHEMA_VERSION,
        "arms": arms,
        "metrics": ["terminal_action", "steps", "protocol_cost", "evidence_count"],
        "claim_boundary": "control-plane counterfactual replay only; no repair-success metric",
    }
    result["manifest_sha256"] = sha256(result)
    return result
