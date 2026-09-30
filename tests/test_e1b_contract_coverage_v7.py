import pytest

from evals.e1b_contract_coverage_v7 import (
    audit_patch_coverage,
    build_coverage_contract,
    require_patch_coverage,
)
from evals.e1b_contract_extractor_v6 import extract_contract
from evals.e1b_editor_adapter_v7 import enrich_payload


def test_coverage_contract_requires_all_visible_participants():
    payload = {
        "problem_statement": "检索预算必须同时受配置和运行时 clamp 约束，不能让配置超过硬上限。",
        "setup_files": ["config/retrieval.json", "src/agents/budget.py"],
    }
    contract = build_coverage_contract(payload, extract_contract(payload["problem_statement"]))
    assert contract["required_participants"] == ["config/retrieval.json", "src/agents/budget.py"]


def test_coverage_gate_detects_v6_style_missing_companion_file():
    contract = {
        "required_participants": ["config/retrieval.json", "src/agents/budget.py"],
    }
    report = audit_patch_coverage(contract, {"src/agents/budget.py": "content"})
    assert report["participant_coverage_complete"] is False
    assert report["missing_required_participants"] == ["config/retrieval.json"]


def test_runtime_coverage_gate_fails_closed_before_patch_application():
    contract = {"required_participants": ["config/retrieval.json", "src/agents/budget.py"]}
    with pytest.raises(ValueError, match="config/retrieval.json"):
        require_patch_coverage(contract, {"src/agents/budget.py": "content"})


def test_coverage_gate_accepts_complete_cross_file_patch():
    contract = {
        "required_participants": ["src/agents/tool_result.py", "src/service/task_adapter.py"],
    }
    patch = {"src/agents/tool_result.py": "a", "src/service/task_adapter.py": "b"}
    assert audit_patch_coverage(contract, patch)["participant_coverage_complete"] is True


def test_v7_payload_combines_behavior_and_participant_contracts():
    payload = {
        "problem_statement": "恢复旧 checkpoint 时必须迁移 version 1 的 approval 字段并保持 version 2 数据不变。",
        "setup_files": ["src/agents/state_migration.py"],
    }
    enriched = enrich_payload(payload)
    assert enriched["deterministic_contract"]["default_transition"] == "identity"
    assert enriched["coverage_contract"]["required_participants"] == ["src/agents/state_migration.py"]
