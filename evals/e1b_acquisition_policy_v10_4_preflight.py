import json

from evals.e1b_acquisition_counterfactual_v10_4 import SCHEMA_VERSION as REPLAY_SCHEMA
from evals.e1b_acquisition_policy_interface_v10_4 import (
    SCHEMA_VERSION,
    action_set_manifest,
    dominance_report,
    sha256,
)

SYNTHETIC_CORPUS = [
    {"name": "interface-parity"},
    {"name": "leakage-rejection"},
    {"name": "deterministic-tie"},
    {"name": "admissibility"},
    {"name": "replay-isolation"},
    {"name": "dominance-report"},
    {"name": "budget-safety"},
    {"name": "stable-hashes"},
]


def report():
    payload = {
        "protocol": "e1b-v10-4-policy-interface-offline-preflight-v1",
        "schema_version": SCHEMA_VERSION,
        "replay_schema_version": REPLAY_SCHEMA,
        "action_set_manifest_sha256": action_set_manifest(),
        "dominance_report": dominance_report(),
        "synthetic_case_count": len(SYNTHETIC_CORPUS),
        "synthetic_corpus_sha256": sha256(SYNTHETIC_CORPUS),
        "provider_calls": 0,
        "live_runner_exists": False,
        "learned_policy_exists": False,
    }
    return payload


if __name__ == "__main__":
    print(json.dumps(report(), ensure_ascii=False, indent=2))
