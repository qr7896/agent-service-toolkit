from evals.e1c_evidence import excerpts


def test_task_agnostic_excerpt_selection_excludes_tests(tmp_path):
    (tmp_path / "module.py").write_text("def special_thing():\n    return 1\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_module.py").write_text("def special_thing():\n    return 0\n", encoding="utf-8")
    found = excerpts("Fix `special_thing` behavior", tmp_path)
    assert [item["path"] for item in found] == ["module.py"]
    assert "return 1" in found[0]["text"]
