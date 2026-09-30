import pytest

from evals.e1b_behavior_witness_v8 import audit_behavior_witness, require_behavior_witness
from evals.e1b_contract_extractor_v6 import extract_contract


def test_behavior_witness_requires_target_and_preserved_named_states():
    contract = extract_contract("错误映射为 failed，保持 pending 不变。")
    report = audit_behavior_witness(contract, {"src/status.py": "return 'failed'"})
    assert report["missing_target_witnesses"] == []
    assert report["missing_preservation_witnesses"] == ["pending"]
    assert report["behavior_witness_complete"] is False


def test_behavior_witness_accepts_explicit_state_branches():
    contract = extract_contract("错误映射为 failed，保持 pending 不变。")
    patch = {"src/status.py": "if state == 'pending': return 'pending'\nreturn 'failed'"}
    assert require_behavior_witness(contract, patch)["behavior_witness_complete"] is True


def test_behavior_witness_understands_version_equality_form():
    contract = extract_contract("迁移 version 1，并保持 version 2 不变。")
    patch = {"src/migrate.py": "if version == 1: migrate()\nif version == 2: return data"}
    assert audit_behavior_witness(contract, patch)["behavior_witness_complete"] is True


def test_behavior_witness_fails_closed_on_missing_legacy_or_current_state():
    contract = extract_contract("迁移 version 1，并保持 version 2 不变。")
    with pytest.raises(ValueError, match="version 2"):
        require_behavior_witness(contract, {"src/migrate.py": "if version == 1: migrate()"})
