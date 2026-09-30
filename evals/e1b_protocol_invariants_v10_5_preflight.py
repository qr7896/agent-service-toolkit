import json

from evals.e1b_acquisition_policy_interface_v10_4 import sha256
from evals.e1b_protocol_invariants_v10_5 import INVARIANT_IDS, SCHEMA_VERSION, evaluate_invariants


def report():
    invariants = evaluate_invariants()
    return {
        "protocol": "e1b-v10-5-protocol-invariants-offline-preflight-v1",
        "schema_version": SCHEMA_VERSION,
        "invariant_ids": list(INVARIANT_IDS),
        "invariant_count": len(INVARIANT_IDS),
        "all_passed": invariants["all_passed"],
        "fixture_sha256": invariants["fixture_sha256"],
        "action_set_manifest_sha256": invariants["action_set_manifest_sha256"],
        "report_sha256": sha256(invariants),
        "provider_calls": 0,
        "live_runner_exists": False,
    }


if __name__ == "__main__":
    print(json.dumps(report(), ensure_ascii=False, indent=2))
