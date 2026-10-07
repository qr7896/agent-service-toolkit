import copy
import hashlib

import pytest

from evals import e1c_evaluation_2_reference_scope as scope


def fixture(tmp_path, monkeypatch, package="alpha", source=None):
    path = tmp_path / package
    path.mkdir()
    raw = source or b"class Schema:\n    pass\nclass DateTime:\n    pass\n"
    (path / "fields.py").write_bytes(raw)
    monkeypatch.setattr(scope, "git_blob", lambda *args: raw.replace(b"\r\n", b"\n"))
    public = [{"kind": "fixture_class", "name": "Example", "bases": [{"kind": "reference", "name": "Schema"}],
               "fields": [{"name": "date", "value": {"kind": "call", "callee": {"kind": "attribute",
                          "owner": {"kind": "reference", "name": "fields"}, "name": "DateTime"},
                          "arguments": [], "keywords": {"required": {"kind": "literal", "value": True}}}}]}]
    frozen = {"base_commit": "b" * 40, "windows": [{"path": package + "/fields.py", "source_sha256": hashlib.sha256(raw).hexdigest()}],
              "public_fixture_facts": [{"facts": public}]}
    payload = {"setup_source": f"from {package}.fields import Schema\nfrom {package} import fields\nclass Example(Schema):\n    date = fields.DateTime(required=True)",
               "target_action": "Example()"}
    return payload, frozen


@pytest.mark.parametrize("package", ["alpha", "beta"])
def test_conditional_structure_not_explicit_import_or_trusted(tmp_path, monkeypatch, package):
    payload, frozen = fixture(tmp_path, monkeypatch, package)
    before = copy.deepcopy((payload, frozen))
    result = scope.inspect_scope(payload, frozen, tmp_path)
    assert result["status"] == "conditional_structure_supported"
    assert {r["public_reference"] for r in result["scope_assumptions"]} == {"Schema", "fields.DateTime"}
    assert result["strict_program_evidence"]["unknown"] == ["public_fixture_constraint_unproven"]
    assert not result["trusted_reproducer"] and not result["semantic_alignment_proven"]
    assert (payload, frozen) == before


@pytest.mark.parametrize("replacement", ["fields.DateTime(required=False)", "fields.Other(required=True)", "DateTime(required=True)"])
def test_changed_value_or_full_reference_path_rejected(tmp_path, monkeypatch, replacement):
    payload, frozen = fixture(tmp_path, monkeypatch)
    payload["setup_source"] += "\nfrom alpha import DateTime"
    payload["setup_source"] = payload["setup_source"].replace("fields.DateTime(required=True)", replacement)
    assert scope.inspect_scope(payload, frozen, tmp_path)["status"] == "rejected"


def test_model_alias_not_required_to_have_same_spelling(tmp_path, monkeypatch):
    payload, frozen = fixture(tmp_path, monkeypatch)
    payload["setup_source"] = payload["setup_source"].replace("import fields", "import fields as f").replace("fields.DateTime", "f.DateTime")
    assert scope.inspect_scope(payload, frozen, tmp_path)["status"] == "conditional_structure_supported"


def test_direct_import_of_same_qualified_object_keeps_conditional_scope(tmp_path, monkeypatch):
    payload, frozen = fixture(tmp_path, monkeypatch)
    payload["setup_source"] += "\nfrom alpha.fields import DateTime"
    payload["setup_source"] = payload["setup_source"].replace("fields.DateTime(required=True)", "DateTime(required=True)")
    assert scope.inspect_scope(payload, frozen, tmp_path)["status"] == "conditional_structure_supported"


def test_frozen_definition_shadowing_is_unknown(tmp_path, monkeypatch):
    payload, frozen = fixture(tmp_path, monkeypatch, source=b"class Schema:\n    pass\nSchema = other\nclass DateTime:\n    pass\n")
    assert scope.inspect_scope(payload, frozen, tmp_path)["status"] == "unknown"


def test_other_library_same_leaf_does_not_supply_frozen_scope(tmp_path, monkeypatch):
    payload, frozen = fixture(tmp_path, monkeypatch)
    payload["setup_source"] = payload["setup_source"].replace("alpha", "foreign")
    assert scope.inspect_scope(payload, frozen, tmp_path)["status"] == "unknown"


def test_actual_base_source_change_stays_unknown(tmp_path, monkeypatch):
    payload, frozen = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(scope, "git_blob", lambda *args: b"another base")
    assert scope.inspect_scope(payload, frozen, tmp_path)["status"] == "unknown"


def test_alias_shadow_still_rejected(tmp_path, monkeypatch):
    payload, frozen = fixture(tmp_path, monkeypatch)
    payload["setup_source"] += "\nSchema = other"
    assert scope.inspect_scope(payload, frozen, tmp_path)["status"] == "rejected"
