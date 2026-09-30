import json

from evals.e1b_semantic_evidence_ir_v10 import manifest_sha256
from evals.e1b_verification_decision_v10_1 import MAX_ESCALATIONS, PRIORITY, SCHEMA_VERSION

SYNTHETIC_CORPUS = [
    {"name": "all-satisfied"},
    {"name": "contradiction"},
    {"name": "ambiguity"},
    {"name": "unsupported"},
    {"name": "mixed-precedence"},
    {"name": "budget-exhaustion"},
    {"name": "kind-accounting"},
]


def report():
    return {
        "protocol": "e1b-v10-1-verification-decision-offline-preflight-v1",
        "schema_version": SCHEMA_VERSION,
        "priority": list(PRIORITY),
        "max_escalations": MAX_ESCALATIONS,
        "synthetic_case_count": len(SYNTHETIC_CORPUS),
        "synthetic_corpus_sha256": manifest_sha256(SYNTHETIC_CORPUS),
        "provider_calls": 0,
        "live_runner_exists": False,
        "ready_for_offline_validation": True,
    }


if __name__ == "__main__":
    print(json.dumps(report(), ensure_ascii=False, indent=2))
