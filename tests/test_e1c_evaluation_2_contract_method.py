import json

import pytest

from evals.e1c_evaluation_2_contract_method import build_pair, coverage_input, parse_response

FROZEN = {"issue": "The public call should complete for the reported input.", "input_sha256": "input",
          "candidate_paths": ["pkg/engine.py"]}


def payload():
    return {"issue_quote": FROZEN["issue"], "expected_quote": "should complete for the reported input",
            "oracle": "call_completes", "setup_source": "from pkg.engine import public_api",
            "control_action": "public_api(0)", "target_action": "public_api(1)", "assertion": ""}


def test_response_classifies_abstention_without_synthesizing_source():
    assert parse_response('{"abstain_reason":"No observable requirement"}', "B")["status"] == "abstained"
    assert parse_response('```json\n{"source":"assert False"}\n```', "A")["payload"]["source"] == "assert False"
    with pytest.raises(ValueError, match="input_echo"):
        parse_response('{"issue":"echo","windows":[]}', "A")
    with pytest.raises(ValueError, match="empty"):
        parse_response("", "B")


def test_controller_assembles_completion_oracle_and_shared_contract():
    control, target = build_pair(payload(), FROZEN)
    assert "public_api(0)" in control["source"] and "public_api(1)" in target["source"]
    assert "assert _e1c_control_done" in control["source"]
    assert "assert _e1c_target_done" in target["source"]
    assert control["contract_sha256"] == target["contract_sha256"]
    assert target["trusted_reproducer"] is False


def test_contract_rejects_oracle_drift_catches_and_dummy_control():
    for update, message in (
        ({"expected_quote": "an invented requirement"}, "quote"),
        ({"assertion": "assert observed == 42"}, "value_assertion"),
        ({"control_action": "try:\n    public_api(0)\nexcept Exception:\n    pass"}, "swallows"),
        ({"control_action": "len([])"}, "real_call"),
    ):
        with pytest.raises(ValueError, match=message):
            build_pair({**payload(), **update}, FROZEN)


def test_value_relation_is_structural_not_an_automatic_semantic_verdict():
    item = {**payload(), "oracle": "value_relation", "target_action": "observed = public_api(1)",
            "assertion": "assert observed == 1"}
    _, target = build_pair(item, FROZEN)
    assert "assert observed == 1" in target["source"]
    assert target["trusted_reproducer"] is False
    with pytest.raises(ValueError, match="comparison"):
        build_pair({**item, "assertion": "assert True"}, FROZEN)


def test_traceback_coverage_never_reads_original_tests_and_ignores_task_labels(tmp_path):
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "engine.py").write_text("def execute_case(value):\n    return value\n\ndef unrelated(value):\n    return 0\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_engine.py").write_text("def execute_case():\n    assert False  # secret assertion sentinel\n", encoding="utf-8")
    issue = 'The API execute_case fails.\nFile "/installed/pkg/engine.py", line 2, in execute_case'
    seed = {"issue": issue, "issue_sha256": "issue", "base_commit": "a" * 40, "windows": [], "instance_id": "label-a"}
    a = coverage_input(seed, tmp_path)
    b = coverage_input({**seed, "instance_id": "different-label"}, tmp_path)
    assert a == b
    assert a["windows"][0]["path"] == "pkg/engine.py"
    assert a["windows"][0]["origin"] == "issue_traceback_production"
    assert "secret assertion sentinel" not in json.dumps(a)
    assert all(not row["path"].startswith("tests/") for row in a["windows"])


def test_contract_json_envelope_uses_system_instruction_and_task_free_context():
    from evals.e1c_evaluation_2_contract_ab_dev import messages

    result = messages({"issue": FROZEN["issue"], "windows": [], "instance_id": "never-send-task-id"}, "B")
    assert result[0].type == "system" and "positive" not in result[1].content
    assert "never-send-task-id" not in "".join(item.content for item in result)
    assert "control_action" in result[0].content
