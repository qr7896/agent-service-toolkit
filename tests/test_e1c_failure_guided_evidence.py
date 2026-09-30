from evals.e1c_failure_guided_evidence import locate, windows


def test_unique_failing_test_stem_locates_source_without_manual_id(tmp_path):
    source = tmp_path / "pkg" / "autodetector.py"
    source.parent.mkdir()
    source.write_text("def alter_fields():\n    return 'field=field'\n", encoding="utf-8")
    log = 'FAIL: test_alter_field\n  File "/testbed/tests/migrations/test_autodetector.py", line 20\n'
    found = locate("Alter field dependency", log, tmp_path)
    assert found == [{"path": "pkg/autodetector.py", "confidence": 80,
                      "origin": "unique_failing_test_stem"}]
    assert windows("Alter field dependency", log, tmp_path)[0]["path"] == "pkg/autodetector.py"


def test_test_files_and_setup_are_not_source_candidates(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "tests.py").write_text("def test_issue(): pass\n", encoding="utf-8")
    (tmp_path / "setup.py").write_text("def setup(): pass\n", encoding="utf-8")
    log = 'ERROR: issue\n  File "/testbed/pkg/tests.py", line 1\n'
    assert locate("issue", log, tmp_path) == []


def test_explicit_source_path_is_used_when_traceback_has_no_source(tmp_path):
    source = tmp_path / "pkg" / "core.py"
    source.parent.mkdir()
    source.write_text("def repair():\n    return 1\n", encoding="utf-8")
    found = locate("Bug in pkg/core.py repair", "FAILED test_missing", tmp_path)
    assert found[0]["origin"] == "explicit_issue_path"
