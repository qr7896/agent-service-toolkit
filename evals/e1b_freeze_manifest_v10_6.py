import hashlib
import json
import platform
import sys
from pathlib import Path

from evals.e1b_acquisition_counterfactual_v10_4 import MAX_REPLAY_STEPS
from evals.e1b_acquisition_policy_interface_v10_4 import action_set_manifest
from evals.e1b_evidence_acquisition_runtime_v10_3 import MAX_STEPS as ACQUISITION_MAX_STEPS
from evals.e1b_evidence_acquisition_v10_3 import MAX_ACQUISITION_COST
from evals.e1b_protocol_invariants_v10_5 import evaluate_invariants
from evals.e1b_verification_control_runtime_v10_2 import MAX_STEPS as CONTROL_MAX_STEPS
from evals.e1b_verification_decision_v10_1 import MAX_ESCALATIONS

SCHEMA_VERSION = "e1b-freeze-manifest-v1"
ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "evals/e1b_semantic_evidence_ir_v10.py",
    "evals/e1b_verification_decision_v10_1.py",
    "evals/e1b_verification_control_runtime_v10_2.py",
    "evals/e1b_evidence_acquisition_v10_3.py",
    "evals/e1b_evidence_acquisition_runtime_v10_3.py",
    "evals/e1b_acquisition_policy_interface_v10_4.py",
    "evals/e1b_acquisition_counterfactual_v10_4.py",
    "evals/e1b_protocol_invariants_v10_5.py",
    "docs/research/E1B_V10_SEMANTIC_EVIDENCE_IR_SPEC.md",
    "docs/research/E1B_V10_1_VERIFICATION_DECISION_POLICY.md",
    "docs/research/E1B_V10_2_VERIFICATION_CONTROL_RUNTIME.md",
    "docs/research/E1B_V10_3_EVIDENCE_ACQUISITION_PROTOCOL.md",
    "docs/research/E1B_V10_4_POLICY_INTERFACE_AND_REPLAY.md",
    "docs/research/E1B_V10_5_PROTOCOL_INVARIANTS.md",
)

SCHEMAS = {
    "semantic_evidence_ir": "e1b-semantic-evidence-ir-v1",
    "verification_decision": "e1b-verification-decision-v1",
    "verification_control_runtime": "e1b-verification-control-runtime-v1",
    "evidence_acquisition": "e1b-evidence-acquisition-v1",
    "evidence_acquisition_runtime": "e1b-evidence-acquisition-runtime-v1",
    "policy_interface": "e1b-acquisition-policy-interface-v1",
    "counterfactual_replay": "e1b-acquisition-counterfactual-replay-v1",
    "protocol_invariants": "e1b-protocol-invariants-v1",
}

EXCLUDED_SOURCES = (
    "contaminated_original_six_TEST_fixtures_and_outcomes",
    "replacement_heldout_content_and_outcomes",
    "repeated_DEV_outcomes",
    "SERBench_private_and_Test500",
)


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_manifest(root=ROOT):
    root = Path(root)
    files = {}
    for relative in REQUIRED_FILES:
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        files[relative] = _sha256_bytes(path.read_bytes())
    invariants = evaluate_invariants()
    content = {
        "schema_version": SCHEMA_VERSION,
        "files": dict(sorted(files.items())),
        "schemas": SCHEMAS,
        "bounds": {
            "max_escalations": MAX_ESCALATIONS,
            "control_max_steps": CONTROL_MAX_STEPS,
            "acquisition_max_steps": ACQUISITION_MAX_STEPS,
            "max_acquisition_cost": MAX_ACQUISITION_COST,
            "max_replay_steps": MAX_REPLAY_STEPS,
        },
        "action_set_manifest_sha256": action_set_manifest(),
        "protocol_invariant_report_sha256": _sha256_bytes(canonical(invariants).encode()),
        "protocol_invariant_fixture_sha256": invariants["fixture_sha256"],
        "excluded_sources": list(EXCLUDED_SOURCES),
        "provider_calls": 0,
        "live_runner_exists": False,
        "claim_boundary": "protocol freeze and audit reproducibility only; no repair efficacy claim",
    }
    content["content_manifest_sha256"] = _sha256_bytes(canonical(content).encode())
    return content


def environment_metadata(root=ROOT):
    root = Path(root)
    lockfile = root / "uv.lock"
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform_system": platform.system(),
        "platform_machine": platform.machine(),
        "byteorder": sys.byteorder,
        "uv_lock_sha256": _sha256_bytes(lockfile.read_bytes()) if lockfile.is_file() else None,
    }


def verify_manifest(manifest, root=ROOT):
    try:
        current = content_manifest(root)
    except FileNotFoundError as exc:
        return {"valid": False, "reason": "missing_required_file", "detail": str(exc)}
    if manifest.get("schema_version") != SCHEMA_VERSION:
        return {"valid": False, "reason": "schema_mismatch"}
    if manifest.get("schemas") != SCHEMAS:
        return {"valid": False, "reason": "component_schema_drift"}
    if manifest.get("bounds") != current["bounds"]:
        return {"valid": False, "reason": "config_drift"}
    if manifest.get("files") != current["files"]:
        return {"valid": False, "reason": "file_hash_mismatch"}
    if manifest.get("action_set_manifest_sha256") != current["action_set_manifest_sha256"]:
        return {"valid": False, "reason": "action_set_drift"}
    if manifest.get("protocol_invariant_report_sha256") != current["protocol_invariant_report_sha256"]:
        return {"valid": False, "reason": "invariant_report_drift"}
    if manifest.get("content_manifest_sha256") != current["content_manifest_sha256"]:
        return {"valid": False, "reason": "content_manifest_mismatch"}
    return {"valid": True, "reason": "verified"}
