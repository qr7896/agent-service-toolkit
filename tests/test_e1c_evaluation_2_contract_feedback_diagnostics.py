import hashlib

import pytest

from evals.e1c_evaluation_2_contract_feedback_diagnostics import (
    oracle_readiness,
    unwrap_known_envelope,
)


def test_known_envelope_only_unwraps_exact_dictionary_without_inventing_action():
    action = {"probe": {"oracle": "call_completes"}}
    result, proof = unwrap_known_envelope({"type": "json_object", "content": action})
    assert result is action and proof["known_envelope_removed"] and not proof["action_invented"]
    extra = {"type": "json_object", "content": action, "shell": "pytest"}
    assert unwrap_known_envelope(extra)[0] is extra  # strict caller rejects extras


@pytest.mark.parametrize("content", ["{\"probe\": {}}", [], {"type": "json_object", "content": {"probe": {}}}])
def test_recursive_string_or_ambiguous_envelope_not_accepted(content):
    with pytest.raises(ValueError):
        unwrap_known_envelope({"type": "json_object", "content": content})


@pytest.mark.parametrize("kind,line,status", [("AssertionError", 2, "predicate_false_semantics_unverified"),
    ("TypeError", 2, "oracle_evaluation_error_requires_feedback"), ("TypeError", 1, "unknown")])
def test_failure_at_predicate_is_not_constructor_failure(kind, line, status):
    source = "result = api()\nassert result['x'] == 1\n"
    sha = hashlib.sha256(source.encode()).hexdigest()
    value = oracle_readiness({"source": source, "probe_sha256": sha}, {"probe_sha256": sha,
        "runs": [{"returncode": 1, "log_tail": f'Traceback:\n  File "/e1c2_probe.py", line {line}, in <module>\n{kind}: failure'}]}, "value_relation")
    assert value["rows"][0]["status"] == status
    assert value["untrusted_trace_only"] and value["not_a_trust_certificate"] and not value["semantic_alignment_proven"]


def test_binding_mismatch_cannot_justify_feedback():
    with pytest.raises(ValueError):
        oracle_readiness({"source": "x = 1", "probe_sha256": "wrong"}, {"probe_sha256": "wrong"}, "value_relation")
