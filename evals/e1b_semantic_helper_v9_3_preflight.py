import json

from evals.e1b_semantic_helper_v9_3 import MAX_HELPER_DEPTH, SCHEMA_VERSION, corpus_sha256

SYNTHETIC_CORPUS = [
    {"name": "helper-target", "kind": "change", "source": "failed", "target": "error"},
    {"name": "helper-identity", "kind": "identity", "source": "pending"},
    {"name": "wrong-target", "kind": "change", "source": "failed", "target": "error"},
    {"name": "side-effect", "kind": "change", "source": "failed"},
    {"name": "nested-depth", "kind": "change", "source": "failed"},
    {"name": "typed-bool-int", "kind": "change", "source": False, "target": True},
    {"name": "match-helper", "kind": "identity", "source": "pending"},
]


def report():
    return {
        "protocol": "e1b-v9-3-offline-preflight-v1",
        "schema_version": SCHEMA_VERSION,
        "max_helper_depth": MAX_HELPER_DEPTH,
        "synthetic_case_count": len(SYNTHETIC_CORPUS),
        "synthetic_corpus_sha256": corpus_sha256(SYNTHETIC_CORPUS),
        "provider_calls": 0,
        "live_runner_exists": False,
        "ready_for_offline_validation": True,
    }


if __name__ == "__main__":
    print(json.dumps(report(), ensure_ascii=False, indent=2))
