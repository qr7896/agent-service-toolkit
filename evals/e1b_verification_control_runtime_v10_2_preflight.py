import json

from evals.e1b_semantic_evidence_ir_v10 import manifest_sha256
from evals.e1b_verification_control_runtime_v10_2 import MAX_STEPS, SCHEMA_VERSION
from evals.e1b_verification_decision_v10_1 import MAX_ESCALATIONS

SYNTHETIC_CORPUS = [
    {"name": "unsupported-resolved"},
    {"name": "ambiguity-disambiguated"},
    {"name": "contradiction-immediate"},
    {"name": "budget-exhaustion"},
    {"name": "max-step-guard"},
    {"name": "duplicate-id"},
    {"name": "typed-bool-int"},
    {"name": "deterministic-trace"},
]


def report():
    return {
        "protocol": "e1b-v10-2-control-runtime-offline-preflight-v1",
        "schema_version": SCHEMA_VERSION,
        "max_steps": MAX_STEPS,
        "max_escalations": MAX_ESCALATIONS,
        "synthetic_case_count": len(SYNTHETIC_CORPUS),
        "synthetic_corpus_sha256": manifest_sha256(SYNTHETIC_CORPUS),
        "provider_calls": 0,
        "live_runner_exists": False,
        "ready_for_offline_validation": True,
    }


if __name__ == "__main__":
    print(json.dumps(report(), ensure_ascii=False, indent=2))
