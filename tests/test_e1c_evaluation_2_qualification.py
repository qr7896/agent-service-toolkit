import copy
import hashlib

import pytest

from evals.e1c_evaluation_2_qualification import inspect_program, qualify, structure_status

ISSUE = "Please expose `flag` in `Api.__init__()`.\n"
PAYLOAD = {"setup_source": "from core import Api\nvalues = ['a', 'b']", "target_action": "Api(flag=True)",
           "control_action": "Api()", "expected_quote": ISSUE, "assertion": "", "oracle": "call_completes"}
OBSERVATION = {"schema": "e1c2-source-bound-exception-observation-v2", "original_probe_sha256": "bound",
               "canonical_git_and_effective_file_hash_required": True, "returncode": 1,
               "records": [{"declared_missing_keyword": "flag"}]}


def frozen(tmp_path):
    source = b"class Api:\n    def __init__(self):\n        pass\n"
    (tmp_path / "core.py").write_bytes(source)
    return {"issue": ISSUE, "windows": [{"path": "core.py", "source_sha256": hashlib.sha256(source).hexdigest()}],
            "public_fixture_facts": [{"facts": [{"kind": "fixture_binding", "name": "values", "value": {
                "kind": "list", "items": [{"kind": "literal", "value": "a"}, {"kind": "literal", "value": "b"}]}}]}]}


def result(tmp_path, payload=None, observation=None):
    return qualify(payload or PAYLOAD, frozen(tmp_path), tmp_path, {"probe_sha256": "bound"},
                   observation or OBSERVATION, normal_controls_pass=True, target_repeatable_failure=True)


def test_supported_mechanism_is_only_candidate_not_semantic_certificate(tmp_path):
    value = result(tmp_path)
    assert value["status"] == "mechanism_supported_candidate"
    assert not value["trusted_reproducer"] and not value["semantic_alignment_proven"] and not value["Gold_used"]


def test_same_exception_wrong_public_values_rejected(tmp_path):
    value = result(tmp_path, {**PAYLOAD, "setup_source": "from core import Api\nvalues = ['a']"})
    assert value["status"] == "rejected" and "public_fixture_constraint_changed" in value["rejected"]


@pytest.mark.parametrize("setup", ["from core import Api\nApi = other", "from core import Api\nApi.method = other",
                                   "from core import Api\nsetattr(Api, 'method', other)"])
def test_import_shadow_mutation_and_dynamic_capability_rejected(tmp_path, setup):
    assert result(tmp_path, {**PAYLOAD, "setup_source": setup})["status"] == "rejected"


def test_instance_mutation_stays_unknown_not_universal_denial(tmp_path):
    value = result(tmp_path, {**PAYLOAD, "setup_source": PAYLOAD["setup_source"] + "\nobj.state = 3"})
    assert value["status"] == "unknown" and "instance_or_container_mutation_unproven" in value["unknown"]


def test_missing_public_fixture_is_unknown_not_assumed_preserved(tmp_path):
    assert result(tmp_path, {**PAYLOAD, "setup_source": "from core import Api"})["status"] == "unknown"


def test_another_probe_observation_rejected(tmp_path):
    assert result(tmp_path, observation={**OBSERVATION, "original_probe_sha256": "another"})["status"] == "rejected"


def test_no_public_exception_match_is_only_behavior_candidate(tmp_path):
    value = result(tmp_path, observation={**OBSERVATION, "records": []})
    assert value["status"] == "behavior_candidate_mechanism_unproven" and not value["trusted_reproducer"]


def test_changed_production_binding_not_normalized_away(tmp_path):
    context = frozen(tmp_path)
    (tmp_path / "core.py").write_bytes(b"class Api:\n    pass\n")
    value = inspect_program(PAYLOAD, context, tmp_path)
    assert "production_binding_source_unverified" in value["rejected"]


def test_bool_vs_integer_public_literal_not_equivalent(tmp_path):
    context = frozen(tmp_path)
    context["public_fixture_facts"][0]["facts"][0] = {"kind": "fixture_binding", "name": "values", "value": {"kind": "literal", "value": True}}
    value = inspect_program({**PAYLOAD, "setup_source": "from core import Api\nvalues = 1"}, context, tmp_path)
    assert "public_fixture_constraint_changed" in value["rejected"]


def test_input_and_observation_not_changed(tmp_path):
    before = copy.deepcopy((PAYLOAD, OBSERVATION))
    result(tmp_path)
    assert (PAYLOAD, OBSERVATION) == before


def test_omitted_public_import_scope_is_unknown_not_fabricated_or_changed():
    assert structure_status({"kind": "qualified_reference", "name": "pkg.DateTime"},
                            {"kind": "reference", "name": "DateTime"}) == "unproven"
    assert structure_status({"kind": "qualified_reference", "name": "pkg.String"},
                            {"kind": "reference", "name": "DateTime"}) == "different"
