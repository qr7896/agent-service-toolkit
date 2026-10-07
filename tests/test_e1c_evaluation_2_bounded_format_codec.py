import json

import pytest

from evals.e1c_evaluation_2_bounded_repro_dev_v3 import parse_action


@pytest.mark.parametrize("value,kind", [({"type": "json_object", "retrieve": "Schema"}, "retrieve"),
                                      ({"type": "json_object", "read": {"path": "core.py", "start_line": 10}}, "read"),
                                      ({"type": "json_object", "abstain_reason": "no observable expectation"}, "abstain_reason"),
                                      ({"type": "json_object", "issue_quote": "production API", "expected_quote": "should complete",
                                        "oracle": "call_completes", "setup_source": "", "control_action": "api([])",
                                        "target_action": "api([1])", "assertion": ""}, "probe")])
def test_known_metadata_normalizes_without_rewriting_payload(value, kind):
    action, payload = parse_action(json.dumps(value))
    assert action == kind
    if kind == "probe":
        assert payload == {k: v for k, v in value.items() if k != "type"}
    else:
        assert payload == value[kind]


@pytest.mark.parametrize("value", [{"type": "json_object", "retrieve": "Schema", "issue": "echo"},
                                   {"type": "json_object", "shell": "read tests"},
                                   {"type": "json_object", "read": {"path": "core.py", "start_line": -1}},
                                   {"type": "unknown", "retrieve": "Schema"}])
def test_unknown_metadata_extra_fields_and_unsupported_tools_still_rejected(value):
    with pytest.raises(ValueError):
        parse_action(json.dumps(value))
