from evals.e1c_evidence_v2 import excerpts


def test_traceback_path_and_symbol_win_over_generic_word_counts(tmp_path):
    package = tmp_path / "src" / "_pytest"
    package.mkdir(parents=True)
    (package / "compat.py").write_text(
        "import os\n\ndef num_mock_patch_args(function):\n    return 1\n",
        encoding="utf-8",
    )
    (package / "cacheprovider.py").write_text("array patch " * 100, encoding="utf-8")
    found = excerpts("/site-packages/_pytest/compat.py: in num_mock_patch_args; patch array", tmp_path)
    assert found[0]["path"] == "src/_pytest/compat.py"
    assert "def num_mock_patch_args" in found[0]["text"]


def test_definition_window_not_file_header_and_tests_excluded(tmp_path):
    source = tmp_path / "module.py"
    source.write_text("import os\n" * 60 + "def stackplot():\n    return 1\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_module.py").write_text("def stackplot():\n    return 0\n", encoding="utf-8")
    found = excerpts("stackplot() fails", tmp_path)
    assert found[0]["path"] == "module.py"
    assert found[0]["start_line"] > 40
    assert "def stackplot" in found[0]["text"]


def test_named_title_class_beats_generic_field_files(tmp_path):
    forms = tmp_path / "auth" / "forms.py"
    forms.parent.mkdir()
    forms.write_text("class AuthenticationForm:\n    pass\n", encoding="utf-8")
    fields = tmp_path / "fields.py"
    fields.write_text("field username\n" * 20, encoding="utf-8")
    found = excerpts("AuthenticationForm's username field lacks maxlength", tmp_path)
    assert found[0]["path"] == "auth/forms.py"
