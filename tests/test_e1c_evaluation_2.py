import hashlib
import json

import pytest

from evals.e1c_evaluation_2 import IDENTITY, LEDGER_SCHEMA, evaluate


def test_feedback_audit_is_bound_to_dev12_and_never_promotes_a_failure():
    identity_bytes = IDENTITY.read_bytes()
    instance_id = json.loads(identity_bytes)["tasks"][0]["instance_id"]
    ledger = {
        "schema": LEDGER_SCHEMA,
        "cohort": "dev12",
        "identity_sha256": hashlib.sha256(identity_bytes).hexdigest(),
        "rows": [
            {
                "instance_id": instance_id,
                "probe_sha256": "a" * 64,
                "returncode": 1,
                "timed_out": False,
                "stdout": "",
                "stderr": "AssertionError: wrong value",
            }
        ],
    }
    audit = evaluate(identity_bytes, ledger)
    assert (audit["attempted_tasks"], audit["candidate_count"], audit["trusted_reproducer_count"]) == (1, 1, 0)
    assert audit["development_gate_passed"] is False
    assert "stderr" not in audit["rows"][0]
    ledger["rows"][0]["instance_id"] = "django__django-12453"
    with pytest.raises(ValueError, match="unknown task"):
        evaluate(identity_bytes, ledger)


def test_public_exception_is_still_only_a_candidate():
    identity_bytes = IDENTITY.read_bytes()
    instance_id = json.loads(identity_bytes)["tasks"][0]["instance_id"]
    ledger = {
        "schema": LEDGER_SCHEMA,
        "cohort": "dev12",
        "identity_sha256": hashlib.sha256(identity_bytes).hexdigest(),
        "rows": [{
            "instance_id": instance_id,
            "probe_sha256": "b" * 64,
            "returncode": 1,
            "timed_out": False,
            "stdout": "",
            "stderr": "ValueError: wrong model",
            "public_exception": {"exception_type": "ValueError", "message": "wrong model"},
        }],
    }
    audit = evaluate(identity_bytes, ledger)
    assert audit["reason_counts"] == {"public_exception_candidate": 1}
    assert audit["trusted_reproducer_count"] == 0
