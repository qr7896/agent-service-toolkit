import pytest

from evals import e1c_evaluation_2_export_chain as checker


def sources(tmp_path, monkeypatch, export="from .schema import Api\n", definition="class Api:\n    pass\n"):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg/__init__.py").write_text(export, encoding="utf-8")
    (tmp_path / "pkg/schema.py").write_text(definition, encoding="utf-8")
    monkeypatch.setattr(checker, "git_blob", lambda workspace, commit, name: (workspace / name).read_bytes().replace(b"\r\n", b"\n"))


def test_relative_export_chain_identity_is_not_runtime_identity(tmp_path, monkeypatch):
    sources(tmp_path, monkeypatch)
    value = checker.export_chain(tmp_path, "pkg.Api", "b" * 40)
    assert value["status"] == "static_chain_supported"
    assert [r["path"] for r in value["chain"]] == ["pkg/__init__.py", "pkg/schema.py"]
    assert not value["runtime_object_identity_proven"]


@pytest.mark.parametrize("export", ["from .schema import Api\nApi = other\n", "from .schema import *\n",
                                   "from .schema import Api\nfrom .schema import Api\n", "from .schema import Api\nexec(code)\n",
                                   "if flag:\n    from .schema import Api\n", "from . import Api\n",
                                   "from .schema import Api\nimport another as Api\n",
                                   "from .schema import Api\nif flag:\n    from another import Api\n"])
def test_shadow_dynamic_star_conditional_or_cycle_unknown(tmp_path, monkeypatch, export):
    sources(tmp_path, monkeypatch, export=export)
    assert checker.export_chain(tmp_path, "pkg.Api", "b" * 40)["status"] == "unknown"


def test_changed_canonical_base_unknown(tmp_path, monkeypatch):
    sources(tmp_path, monkeypatch)
    monkeypatch.setattr(checker, "git_blob", lambda *args: b"different canonical base")
    assert checker.export_chain(tmp_path, "pkg.Api", "b" * 40)["reason"] == "export_source_differs_from_base"


def test_duplicate_module_locations_unknown(tmp_path, monkeypatch):
    sources(tmp_path, monkeypatch)
    (tmp_path / "pkg.py").write_text("class Api: pass\n", encoding="utf-8")
    assert checker.export_chain(tmp_path, "pkg.Api", "b" * 40)["reason"] == "module_missing_or_ambiguous"


def test_protected_package_or_bad_base_rejected(tmp_path):
    with pytest.raises(Exception):
        checker.export_chain(tmp_path, "tests.Api", "b" * 40)
    with pytest.raises(ValueError):
        checker.export_chain(tmp_path, "pkg.Api", "bad")
