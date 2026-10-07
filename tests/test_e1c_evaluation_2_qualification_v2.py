import hashlib

from evals import e1c_evaluation_2_qualification_v2 as auditor


def context(tmp_path):
    source = b"class Api:\n    pass\n"
    (tmp_path / "core.py").write_bytes(source)
    return {"issue": "Public source context", "windows": [{"path": "core.py", "source_sha256": hashlib.sha256(source).hexdigest()}]}


def test_unexposed_dependency_is_unknown_not_corrupt_source(tmp_path):
    frozen = context(tmp_path)
    frozen["windows"] = []
    result = auditor.inspect_program({"setup_source": "from core import Api", "target_action": "Api()"}, frozen, tmp_path)
    assert not result["rejected"] and "unexposed_dependency_source_provenance_unknown" in result["unknown"]


def test_exposed_actual_byte_mismatch_still_rejected(tmp_path):
    frozen = context(tmp_path)
    (tmp_path / "core.py").write_bytes(b"class Api:\n    x = 1\n")
    result = auditor.inspect_program({"setup_source": "from core import Api", "target_action": "Api()"}, frozen, tmp_path)
    assert "production_binding_source_unverified" in result["rejected"]


def test_augmented_assignment_and_deletion_not_claimed_preserved(tmp_path):
    result = auditor.inspect_program({"setup_source": "from core import Api\nvalues = 'known'\nvalues += 'changed'\ndel values",
        "target_action": "Api()"}, context(tmp_path), tmp_path)
    assert "noncanonical_binding_mutation_unproven" in result["unknown"]


def test_nested_audit_restores_original_resolver(tmp_path):
    original = auditor.base.resolve_symbol
    auditor.inspect_program({"setup_source": "from core import Api", "target_action": "Api()"}, context(tmp_path), tmp_path)
    assert auditor.base.resolve_symbol is original
