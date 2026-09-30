import pytest

from evals.e1b_contract_extractor_v6 import extract_contract
from evals.e1b_state_transition_v8 import (
    audit_state_transition_contract,
    build_transition_contract,
    require_state_transition_contract,
)


def contract(statement):
    return build_transition_contract(extract_contract(statement))


def test_builds_change_and_identity_obligations():
    value = contract("错误映射为 failed，保持 pending 不变。")
    assert value["target_obligations"] == [{"state": "failed", "mode": "change"}]
    assert value["preservation_obligations"] == [{"state": "pending", "mode": "identity"}]
    assert value["default_transition"] == "identity"
    assert value["schema_version"] == "e1b-state-transition-v1"


def test_rejects_bare_literals_without_explicit_state_guard():
    report = audit_state_transition_contract(
        contract("错误映射为 failed，保持 pending 不变。"),
        {"src/status.py": "return 'failed'\nDEFAULT = 'pending'"},
    )
    assert report["transition_witness_complete"] is False
    assert {row["state"] for row in report["missing_obligations"]} == {"failed", "pending"}


def test_accepts_explicit_guarded_state_branches():
    patch = {
        "src/status.py": (
            "if status == 'pending':\n    return status\n"
            "if result == 'error':\n    return 'failed'\n"
        )
    }
    assert require_state_transition_contract(
        contract("错误映射为 failed，保持 pending 不变。"), patch
    )["transition_witness_complete"] is True


def test_accepts_version_specific_guards():
    patch = {
        "src/migrate.py": (
            "if version == 1:\n    return migrate(data)\n"
            "if version == 2:\n    return data\n"
        )
    }
    assert require_state_transition_contract(
        contract("迁移 version 1，并保持 version 2 不变。"), patch
    )["transition_witness_complete"] is True


def test_fails_closed_when_identity_branch_is_missing():
    with pytest.raises(ValueError, match="identity:version:2"):
        require_state_transition_contract(
            contract("迁移 version 1，并保持 version 2 不变。"),
            {"src/migrate.py": "if version == 1:\n    return migrate(data)"},
        )


def test_rejects_truthiness_state_collapse_even_with_literals_nearby():
    patch = {
        "src/status.py": (
            "if status:\n    return 'failed'\n"
            "if status == 'pending':\n    return status\n"
        )
    }
    report = audit_state_transition_contract(
        contract("错误映射为 failed，保持 pending 不变。"), patch
    )
    assert report["transition_witness_complete"] is False
    assert report["truthiness_guards"] == ["if status:"]


def test_does_not_treat_plain_if_keyword_as_guarded_value_witness():
    report = audit_state_transition_contract(
        contract("错误映射为 failed，保持 pending 不变。"),
        {"src/status.py": "if ready:\n    note = 'failed'\nPENDING = 'pending'"},
    )
    assert report["transition_witness_complete"] is False
    assert {row["state"] for row in report["missing_obligations"]} == {"failed", "pending"}


def test_audit_is_deterministic_across_patch_mapping_order():
    c = contract("错误映射为 failed，保持 pending 不变。")
    left = {"b.py": "if x == 'failed':\n    pass", "a.py": "if x == 'pending':\n    pass"}
    right = {"a.py": left["a.py"], "b.py": left["b.py"]}
    assert audit_state_transition_contract(c, left) == audit_state_transition_contract(c, right)
