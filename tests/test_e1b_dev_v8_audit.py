from evals.e1b_dev_v8_audit import audit


def reports(resolved=(True, True, False, False), calls=8, tokens=80):
    ids = ["a", "b", "c", "d"]
    v7 = {"rows": [{"instance_id": task, "resolved": old} for task, old in zip(ids, resolved, strict=True)]}
    rows = []
    for task, old in zip(ids, resolved, strict=True):
        rows.append(
            {
                "result_schema": "e1b-r10-v8-result-v1",
                "transition_schema": "e1b-state-transition-v1",
                "instance_id": task,
                "resolved": old,
                "model_calls": 2,
                "failure": None,
                "proposal_coverage": {"participant_coverage_complete": True},
                "final_coverage": {"participant_coverage_complete": True},
                "proposal_transition": {"transition_witness_complete": True},
                "final_transition": {"transition_witness_complete": True},
            }
        )
    v8 = {
        "result_schema": "e1b-r10-v8-result-v1",
        "summary": {
            "tasks": 4,
            "attempted_tasks": 4,
            "model_failures": 0,
            "budget_exhaustions": 0,
            "total_model_calls": calls,
            "total_tokens": tokens,
        },
        "execution": {
            "transition_schema": "e1b-state-transition-v1",
            "contract_coverage_enforced": True,
            "state_transition_enforced": True,
            "test_outcomes_opened": 0,
            "run_complete": True,
        },
        "rows": rows,
    }
    per_call = tokens // calls if calls else 0
    ledger = []
    for index in range(calls):
        ledger.extend(
            [
                {"status": "started", "call": index},
                {"status": "completed", "call": index, "total_tokens": per_call},
            ]
        )
    return v7, v8, ledger


def test_audit_accepts_fewer_calls_when_ledger_matches_summary():
    v7, v8, ledger = reports(calls=6, tokens=60)
    for row in v8["rows"][-2:]:
        row["model_calls"] = 1
        row["resolved"] = False
        row["failure"] = "state_transition_failure"
        row.pop("proposal_coverage", None)
        row.pop("proposal_transition", None)
        row.pop("final_coverage", None)
        row.pop("final_transition", None)
    assert audit(v7, v8, ledger)["protocol_valid"] is True


def test_audit_rejects_schema_mismatch():
    v7, v8, ledger = reports()
    v8["result_schema"] = "wrong"
    assert audit(v7, v8, ledger)["protocol_valid"] is False


def test_audit_rejects_ledger_call_mismatch():
    v7, v8, ledger = reports()
    assert audit(v7, v8, ledger[:-2])["protocol_valid"] is False


def test_audit_rejects_ledger_token_mismatch():
    v7, v8, ledger = reports()
    ledger[-1]["total_tokens"] += 1
    assert audit(v7, v8, ledger)["protocol_valid"] is False


def test_freeze_requires_all_four_resolved_and_no_regression():
    v7, v8, ledger = reports(resolved=(True, True, True, True))
    result = audit(v7, v8, ledger)
    assert result["freeze_ready"] is True
    v8["rows"][0]["resolved"] = False
    result = audit(v7, v8, ledger)
    assert result["freeze_ready"] is False
    assert result["regressed_from_v7"] == ["a"]


def test_audit_allows_missing_final_artifacts_on_proposal_gate_rejection():
    v7, v8, _ = reports(calls=1, tokens=10)
    row = v8["rows"][0]
    v8["rows"] = [row, *v8["rows"][1:]]
    row.update(model_calls=1, resolved=False, failure="state_transition_failure")
    row.pop("proposal_coverage", None)
    row.pop("proposal_transition", None)
    row.pop("final_coverage", None)
    row.pop("final_transition", None)
    v8["summary"]["total_model_calls"] = 1
    v8["summary"]["total_tokens"] = 10
    ledger = [{"status": "started"}, {"status": "completed", "total_tokens": 10}]
    # Other rows represent unattempted rows only in this synthetic partial artifact, so
    # this shape is intentionally not a valid complete 4-task protocol.
    assert audit(v7, v8, ledger)["protocol_valid"] is False


def test_audit_rejects_row_schema_mismatch():
    v7, v8, ledger = reports()
    v8["rows"][0]["transition_schema"] = "wrong"
    assert audit(v7, v8, ledger)["protocol_valid"] is False

def test_fake_four_row_artifact_without_completion_identity_cannot_freeze():
    v7, v8, ledger = reports(resolved=(True, True, True, True))
    v8["execution"].pop("run_complete")
    result = audit(v7, v8, ledger)
    assert result["run_complete"] is False
    assert result["freeze_ready"] is False
    assert result["protocol_valid"] is False


def test_legacy_completion_requires_historical_identity_markers():
    v7, v8, ledger = reports()
    v8["execution"].pop("run_complete")
    v8["execution"].update(
        provider_run_id="e1b-r10-dev-v8",
        provider_ledger_path=".codex\\e1b\\r10-v8\\provider_calls.jsonl",
        evidence_protocol="declared-seed-read-v7-coverage-state-transition",
    )
    result = audit(v7, v8, ledger)
    assert result["run_complete"] is True
    assert result["completion_evidence"] == "legacy-v8-identity-and-4-row"

