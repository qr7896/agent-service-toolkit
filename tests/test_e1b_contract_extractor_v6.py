from evals.e1b_contract_extractor_v6 import extract_contract
from evals.e1b_editor_adapter_v6 import enrich_payload


def test_contract_extracts_preservation_clause():
    contract = extract_contract("恢复旧 checkpoint 时必须迁移 version 1 的 approval 字段并保持 version 2 数据不变。")
    assert contract["target_changes"] == ["恢复旧 checkpoint 时必须迁移 version 1 的 approval 字段"]
    assert contract["preservation_constraints"] == ["version 2 数据不变"]
    assert contract["named_target_values"] == ["version 1"]
    assert contract["named_preserved_values"] == ["version 2"]
    assert contract["default_transition"] == "identity"


def test_contract_marks_negative_constraint_as_preservation():
    contract = extract_contract("工具错误必须映射为 failed，不能在上层被统一标成 completed。")
    assert contract["target_changes"] == ["工具错误必须映射为 failed"]
    assert contract["preservation_constraints"] == ["在上层被统一标成 completed"]
    assert contract["named_target_values"] == ["failed"]
    assert contract["named_preserved_values"] == ["completed"]


def test_enriched_payload_adds_contract_without_gold():
    payload = {"problem_statement": "错误映射为 failed，保持 pending 不变。", "evidence": {"items": []}}
    enriched = enrich_payload(payload)
    assert "deterministic_contract" in enriched
    assert "gold" not in str(enriched).lower()
