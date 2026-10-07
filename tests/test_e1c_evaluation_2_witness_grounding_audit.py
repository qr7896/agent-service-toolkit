from evals.e1c_evaluation_2_witness_grounding_audit import audit, expectation_role


def test_trace_is_not_a_desired_behavior_quote():
    assert expectation_role('File "/testbed/core.py", line 17, in api\n') == "runtime_trace_not_desired_behavior"


def test_executable_quote_not_automatically_an_expectation():
    assert expectation_role("api(data)") == "code_or_literal_not_desired_behavior"


def test_prose_remains_unverified_not_auto_trusted():
    assert expectation_role("The documented API should accept valid inputs.") == "unclassified_requires_semantic_evidence"


def test_exact_public_site_observed_in_both_runs_not_a_certificate():
    site = {"path": "core.py", "line": 17, "source_sha256": "bound"}
    result = audit({"expected_quote": "The API should complete."}, [site], {"runs": [
        {"log_tail": 'File "/testbed/core.py", line 17, in api'},
        {"log_tail": 'File "/testbed/core.py", line 17, in api'},
    ]})
    assert result["public_failure_guard_sites"][0]["status"] == "observed"
    assert not result["trusted_reproducer"] and not result["semantic_alignment_proven"]


def test_another_failure_does_not_count_as_public_guard_reached():
    site = {"path": "core.py", "line": 17, "source_sha256": "bound"}
    result = audit({"expected_quote": "The API should complete."}, [site], {"runs": [
        {"log_tail": 'File "/testbed/validation.py", line 4, in check'},
    ]})
    assert result["public_failure_guard_sites"][0]["status"] == "not_observed"
    assert result["absence_is_not_global_unreachability_proof"] and not result["Gold_used"]
