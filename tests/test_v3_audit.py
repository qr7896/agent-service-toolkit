from evals.v3_audit import audit_artifacts


def artifacts(synthetic=False):
    collection = {
        "protocol": "v3-prospective-collection-v1",
        "collection_id": "c1",
        "trajectory_schema": "v3-trajectory-v1",
    }
    status = {"collection_id": "c1"}
    frozen = {
        "ready": True,
        "synthetic": synthetic,
        "claim_boundary": "Pipeline connectivity only; no efficacy claim.",
        "readiness": {"protocol": "v3-prospective-readiness-v1"},
        "replay": {"protocol": "v3-chronological-replay-v1", "strict_past_only": True},
        "ablation": {"protocol": "v3-memory-ablation-v1"},
        "counterfactual": {"protocol": "v3-counterfactual-replay-v1", "matched_ready_pairs": 1},
    }
    frozen["protocol_manifest"] = {
        "trajectory_schema": "v3-trajectory-v1",
        "readiness": "v3-prospective-readiness-v1",
        "replay": "v3-chronological-replay-v1",
        "ablation": "v3-memory-ablation-v1",
        "counterfactual": "v3-counterfactual-replay-v1",
    }
    return collection, status, frozen


def test_real_passes():
    assert audit_artifacts(*artifacts(False))["passed"] is True


def test_synthetic_rejected_by_default_and_allowed_explicitly():
    values = artifacts(True)
    assert "synthetic_not_real" in audit_artifacts(*values)["blockers"]
    assert audit_artifacts(*values, require_real=False)["passed"] is True


def test_protocol_manifest_mismatch_fails():
    c, s, f = artifacts(False)
    f["protocol_manifest"]["replay"] = "wrong"
    assert "protocol_manifest_mismatch" in audit_artifacts(c, s, f)["blockers"]


def test_required_replay_claim_and_counterfactual_fields_fail_closed():
    c, s, f = artifacts(False)
    f["replay"]["strict_past_only"] = False
    f["claim_boundary"] = ""
    del f["counterfactual"]["matched_ready_pairs"]
    blockers = audit_artifacts(c, s, f)["blockers"]
    assert {"past_only_missing", "claim_boundary_missing", "matched_ready_pairs_missing"}.issubset(
        blockers
    )
