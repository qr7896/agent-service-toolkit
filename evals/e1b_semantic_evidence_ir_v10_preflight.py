import json

from evals.e1b_semantic_evidence_ir_v10 import SCHEMA_VERSION, manifest_sha256

SYNTHETIC_CORPUS = [
    {"name": "coverage-support"},
    {"name": "direct-identity"},
    {"name": "helper-target"},
    {"name": "wrong-target-contradiction"},
    {"name": "effect-risk"},
    {"name": "duplicate-ambiguity"},
    {"name": "typed-bool-int"},
]


def report():
    return {
        "protocol": "e1b-v10-semantic-evidence-ir-offline-preflight-v1",
        "schema_version": SCHEMA_VERSION,
        "synthetic_case_count": len(SYNTHETIC_CORPUS),
        "synthetic_corpus_sha256": manifest_sha256(SYNTHETIC_CORPUS),
        "provider_calls": 0,
        "live_runner_exists": False,
        "ready_for_offline_validation": True,
    }


if __name__ == "__main__":
    print(json.dumps(report(), ensure_ascii=False, indent=2))
