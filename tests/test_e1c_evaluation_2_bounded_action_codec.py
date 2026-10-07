import json

import pytest

from evals.e1c_evaluation_2_bounded_action_codec import parse_action


def probe():
    return {"issue_quote": "supported API", "expected_quote": "should complete", "oracle": "call_completes",
            "setup_source": "", "control_action": "api([])", "target_action": "api([1])", "assertion": ""}


def test_flat_typed_probe_preserves_all_oracle_and_source_fields():
    payload = probe()
    assert parse_action(json.dumps({"type": "probe", **payload})) == ("probe", payload)
    assert parse_action(json.dumps({"probe": payload})) == ("probe", payload)


@pytest.mark.parametrize("kind,value", [("retrieve", "Engine.apply"), ("read", {"path": "core.py", "start_line": 10}),
                                        ("abstain_reason", "missing behavior")])
def test_unique_typed_action_has_identical_canonical_meaning(kind, value):
    assert parse_action(json.dumps({"type": kind, kind: value})) == parse_action(json.dumps({kind: value}))


@pytest.mark.parametrize("value", [{"type": "shell", "shell": "cat tests/answer.py"},
                                   {"type": "retrieve", "read": {"path": "core.py", "start_line": 1}},
                                   {"type": "retrieve", "retrieve": "Engine", "issue": "echo"},
                                   {"type": "probe", **probe(), "execution": {}},
                                   {"type": "probe", **{k: v for k, v in probe().items() if k != "assertion"}},
                                   {"type": "retrieve", "retrieve": "tests/secret.py"}])
def test_conflicting_extra_or_missing_fields_and_paths_still_rejected(value):
    with pytest.raises(ValueError):
        parse_action(json.dumps(value))
