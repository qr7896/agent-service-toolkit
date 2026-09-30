from dataclasses import asdict

from evals.e1b_evidence_acquisition_v10_3 import MAX_ACQUISITION_COST, choose_action, sha256
from evals.e1b_semantic_evidence_ir_v10 import verify
from evals.e1b_verification_decision_v10_1 import decide

SCHEMA_VERSION = "e1b-evidence-acquisition-runtime-v1"
MAX_STEPS = 8


def run(obligations, action_results):
    evidence = []
    attempted = []
    cumulative_cost = 0
    trace = []
    for step in range(MAX_STEPS):
        verification = verify(obligations, evidence)
        policy = decide(obligations, verification, 0)
        if policy["action"] == "BLOCK_PATCH":
            terminal = "BLOCK_PATCH"
            break
        if policy["action"] == "ALLOW_VERIFICATION":
            terminal = "ALLOW_VERIFICATION"
            break
        before = sha256([asdict(row) for row in evidence])
        selection = choose_action(obligations, verification, attempted, cumulative_cost)
        if selection["action"] in {"BYPASS_BLOCK", "EXHAUSTED", "BUDGET_EXHAUSTED"}:
            terminal = "BLOCK_PATCH"
            trace.append({"step": step, **selection, "cumulative_cost": cumulative_cost, "before_evidence_sha256": before, "after_evidence_sha256": before})
            break
        attempted.append(selection["action"])
        cumulative_cost += selection["cost"]
        evidence.extend(action_results.get(selection["action"], []))
        after = sha256([asdict(row) for row in evidence])
        trace.append({"step": step, **selection, "cumulative_cost": cumulative_cost, "before_evidence_sha256": before, "after_evidence_sha256": after})
    else:
        terminal = "BLOCK_PATCH"
        trace.append({"step": MAX_STEPS, "action": "MAX_STEPS", "cost": 0, "reason": "hard_step_bound", "obligation_ids": [], "cumulative_cost": cumulative_cost})
    result = {
        "schema_version": SCHEMA_VERSION,
        "max_steps": MAX_STEPS,
        "max_acquisition_cost": MAX_ACQUISITION_COST,
        "terminal_action": terminal,
        "attempted_actions": attempted,
        "cumulative_cost": cumulative_cost,
        "trace": trace,
        "claim_boundary": "deterministic offline acquisition-control validation only; not learned policy or repair efficacy",
    }
    result["trace_sha256"] = sha256(trace)
    return result
