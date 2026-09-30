import json

from evals.e1b_semantic_dataflow_v9_2 import SCHEMA_VERSION, corpus_sha256

SYNTHETIC_CORPUS = [
    {"name": "alias-identity", "source": "pending", "kind": "identity"},
    {"name": "wrong-target", "source": "failed", "kind": "change", "target": "error"},
    {"name": "bool-int-separation", "source": False, "kind": "change", "target": True},
    {"name": "match-case", "source": "failed", "kind": "change", "target": "error"},
    {"name": "static-dict", "source": "failed", "kind": "change", "target": "error"},
    {"name": "risky-effect", "source": "pending", "kind": "identity"},
]


def report():
    return {
        "protocol": "e1b-v9-2-offline-preflight-v1",
        "schema_version": SCHEMA_VERSION,
        "synthetic_case_count": len(SYNTHETIC_CORPUS),
        "synthetic_corpus_sha256": corpus_sha256(SYNTHETIC_CORPUS),
        "provider_calls": 0,
        "live_runner_exists": False,
        "scope": "synthetic/public generic cases only",
        "ready_for_offline_validation": True,
    }


if __name__ == "__main__":
    print(json.dumps(report(), ensure_ascii=False, indent=2))
