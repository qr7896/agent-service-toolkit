import json

from evals.e1b_evidence_acquisition_v10_3 import ACTIONS, MAX_ACQUISITION_COST, SCHEMA_VERSION, sha256
from evals.e1b_evidence_acquisition_runtime_v10_3 import MAX_STEPS

SYNTHETIC_CORPUS = [
    {"name": "cheapest-compatible"},
    {"name": "coverage-only"},
    {"name": "no-repeat"},
    {"name": "ambiguity-structural"},
    {"name": "contradiction-bypass"},
    {"name": "action-exhaustion"},
    {"name": "cost-exhaustion"},
    {"name": "eventual-resolution"},
]


def report():
    return {
        "protocol": "e1b-v10-3-evidence-acquisition-offline-preflight-v1",
        "schema_version": SCHEMA_VERSION,
        "actions": [action.name for action in ACTIONS],
        "action_costs": {action.name: action.cost for action in ACTIONS},
        "max_acquisition_cost": MAX_ACQUISITION_COST,
        "max_steps": MAX_STEPS,
        "synthetic_case_count": len(SYNTHETIC_CORPUS),
        "synthetic_corpus_sha256": sha256(SYNTHETIC_CORPUS),
        "provider_calls": 0,
        "live_runner_exists": False,
        "ready_for_offline_validation": True,
    }


if __name__ == "__main__":
    print(json.dumps(report(), ensure_ascii=False, indent=2))
