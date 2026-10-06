import json

import pytest

from evals.e1c_evaluation_2_controller_manifest import parse_response
from evals.e1c_evaluation_2_execution_contract import ExecutionContractViolation


def test_plain_legacy_output_gets_controller_owned_manifest():
    parsed = parse_response('{"source":"assert 1 == 1"}', "A")
    assert parsed["execution_owner"] == "controller_grammar"
    assert parsed["payload"] == {"source": "assert 1 == 1"}
    assert parsed["execution_spec"]["mode"] == "direct_script"


def test_metadata_does_not_enable_native_fixture_privileges():
    good = {"source": "assert True", "execution": {"mode": "native", "fixture_source": "official_tests"}}
    assert parse_response(json.dumps(good), "A")["model_execution_metadata_ignored"]
    bad = {**good, "source": "import pytest\npytest.main([])\nassert True"}
    with pytest.raises(ExecutionContractViolation):
        parse_response(json.dumps(bad), "A")


def test_unique_parameterless_entry_derived_but_fixture_parameters_rejected():
    value = parse_response('{"source":"def reproduce():\\n    assert False\\n"}', "A")
    assert value["payload"]["source"].endswith("\n\nreproduce()\n")
    assert value["execution_spec"]["entrypoint"] == "reproduce"
    with pytest.raises(ExecutionContractViolation):
        parse_response('{"source":"def reproduce(testdir):\\n    assert False\\n"}', "A")


def test_other_extra_fields_are_not_silently_accepted():
    with pytest.raises(ValueError):
        parse_response('{"source":"assert True","unapproved_input_echo":"private"}', "A")
