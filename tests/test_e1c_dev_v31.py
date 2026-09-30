from evals.e1c_dev_v31 import _allowed_path, _inspect, _search


def test_source_search_and_inspect_exclude_tests(tmp_path):
    source = tmp_path / "pkg" / "source.py"
    source.parent.mkdir()
    source.write_text("def useful_symbol():\n    return 1\n", encoding="utf-8")
    tests = tmp_path / "tests" / "test_source.py"
    tests.parent.mkdir()
    tests.write_text("def useful_symbol():\n    return 2\n", encoding="utf-8")

    assert _search(tmp_path, "useful_symbol") == ["pkg/source.py"]
    assert _allowed_path(tmp_path, "pkg/source.py")
    assert not _allowed_path(tmp_path, "tests/test_source.py")
    assert not _allowed_path(tmp_path, "../outside.py")
    assert _inspect(tmp_path, "pkg/source.py", "useful_symbol")["text"].startswith(
        "def useful_symbol()"
    )
