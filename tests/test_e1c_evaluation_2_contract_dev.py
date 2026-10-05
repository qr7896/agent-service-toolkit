import hashlib

import pytest

from evals.e1c_evaluation_2_contract_dev import audit_probe


def _candidate(source):
    return {"source": source, "issue_quote": "the public call should work",
            "input_sha256": "frozen", "probe_sha256": hashlib.sha256(source.encode()).hexdigest()}


FROZEN = {"issue": "the public call should work without raising", "input_sha256": "frozen"}


def test_completion_shape_requires_real_call_before_flag():
    sound = "from pkg import api\ncompleted = False\napi.run()\ncompleted = True\nassert completed\n"
    assert audit_probe(FROZEN, _candidate(sound))["shape"] == "completion_after_call"
    no_call = "completed = False\ncompleted = True\nassert completed\n"
    assert audit_probe(FROZEN, _candidate(no_call))["shape"] == "unguarded_completion"
    swallowed = "try:\n    api.run()\nexcept Exception:\n    pass\ncompleted = True\nassert completed\n"
    assert audit_probe(FROZEN, _candidate(swallowed))["shape"] == "exception_swallowed"


def test_value_assertion_remains_semantically_unverified():
    result = audit_probe(FROZEN, _candidate("from pkg import api\nassert api.run() == 2\n"))
    assert result == {"shape": "value_comparison", "semantic_status": "unverified"}
    with pytest.raises(ValueError, match="public-issue span"):
        audit_probe(FROZEN, {**_candidate("assert True"), "issue_quote": "invented outcome"})
    with pytest.raises(ValueError, match="digest differs"):
        audit_probe(FROZEN, {**_candidate("assert True"), "source": "assert False"})
