from __future__ import annotations

import json

from evals.e1c_aci_evidence import extend


def test_search_reveals_source_and_progresses_to_next_file(tmp_path):
    for name in ("a.py", "b.py"):
        (tmp_path / name).write_text("def target():\n    return 1\n", encoding="utf-8")
    windows = []
    raw = json.dumps({"search": {"query": "target"}})
    first = extend(tmp_path, windows, ["a.py", "b.py"], raw, "Search results")
    second = extend(tmp_path, windows, ["a.py", "b.py"], raw, "Search results")
    assert [item["path"] for item in windows] == ["a.py", "b.py"]
    assert all("def target" in item["text"] for item in windows)
    assert "Original-base source window" in first + second


def test_rejected_edit_reveals_only_safe_original_source(tmp_path):
    (tmp_path / "good.py").write_text("def target():\n    return 1\n", encoding="utf-8")
    (tmp_path / "test_bad.py").write_text("def target():\n    return 1\n", encoding="utf-8")
    windows = []
    raw = json.dumps({"edits": [{"path": "good.py", "old": "def target():", "new": "x"}]})
    extend(tmp_path, windows, [], raw, "Action rejected: old text mismatch")
    assert windows[0]["origin"] == "aci_rejected_edit_original_source"
    assert "return 1" in windows[0]["text"]
    unsafe = json.dumps({"edits": [{"path": "test_bad.py", "old": "def target():", "new": "x"}]})
    extend(tmp_path, windows, [], unsafe, "Action rejected: path not exposed")
    assert len(windows) == 1
