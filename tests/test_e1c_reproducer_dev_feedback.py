from evals.e1c_reproducer_dev_feedback import classify_probe_outcome
from evals.e1c_strict_successor_expected_failure import FailureContract


def test_probe_feedback_keeps_environment_failures_out_of_trusted_count():
    base = {"returncode": 1, "timed_out": False, "stdout": "", "stderr": ""}
    assert classify_probe_outcome(**(base | {"stderr": "ModuleNotFoundError: mpmath"}))["reason"] == "setup_or_collection_error"
    assertion = classify_probe_outcome(**(base | {"stderr": "AssertionError: wrong value"}))
    assert assertion["candidate_prepatch_failure"] is True
    assert assertion["trusted_reproducer"] is False
    assert classify_probe_outcome(**(base | {"stderr": "ValueError: unrelated"}))["reason"] == "unrelated_or_unclassified_failure"
    assert classify_probe_outcome(**(base | {"timed_out": True}))["reason"] == "timeout"
    contract = FailureContract("ValueError", "wrong model")
    matched = classify_probe_outcome(**(base | {"stderr": "ValueError: wrong model"}), public_exception=contract)
    assert matched["reason"] == "public_exception_candidate"
    assert matched["trusted_reproducer"] is False
