import pytest

from evals.safe_workspace import SafeWorkspace


def test_list_read_search_and_metrics(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/a.py").write_text("def alpha():\\n    return 1\\n")
    (tmp_path / "src/b.py").write_text("def beta():\\n    return alpha()\\n")
    ws = SafeWorkspace(tmp_path)
    assert ws.list_files() == ["src/a.py", "src/b.py"]
    assert "alpha" in ws.read_text("src/a.py")
    hits = ws.search_text("alpha")
    assert {h["path"] for h in hits} == {"src/a.py", "src/b.py"}
    summary = ws.evidence_summary()
    assert summary["read_calls"] >= 3 and summary["bytes_read"] > 0


@pytest.mark.parametrize("path", ["../x", "/tmp/x", "C:/x", ".git/config", ".env"])
def test_read_escape_and_protected_blocked(tmp_path, path):
    ws = SafeWorkspace(tmp_path)
    with pytest.raises(PermissionError) as raised:
        ws.read_text(path)
    expected = "protected_path" if path.startswith((".git", ".env")) else "path_denied"
    assert raised.value.event["error_type"] == expected
    assert ws.events[-1] == raised.value.event


def test_not_found_is_structured(tmp_path):
    ws = SafeWorkspace(tmp_path)
    with pytest.raises(FileNotFoundError) as raised:
        ws.read_text("missing.py")
    assert raised.value.event["error_type"] == "not_found"


def test_read_budget(tmp_path):
    (tmp_path / "big.txt").write_text("x" * 11)
    ws = SafeWorkspace(tmp_path, max_read_bytes=10)
    with pytest.raises(PermissionError) as raised:
        ws.read_text("big.txt")
    assert raised.value.event["error_type"] == "single_file_budget_exceeded"


def test_search_limit(tmp_path):
    (tmp_path / "a.txt").write_text(chr(10).join(["x", "x", "x"]) + chr(10))
    ws = SafeWorkspace(tmp_path)
    assert len(ws.search_text("x", max_results=2)) == 2


def test_total_read_byte_budget(tmp_path):
    (tmp_path / "a.txt").write_text("12345")
    (tmp_path / "b.txt").write_text("67890")
    ws = SafeWorkspace(tmp_path, max_total_bytes=9)
    ws.read_text("a.txt")
    with pytest.raises(PermissionError) as raised:
        ws.read_text("b.txt")
    assert raised.value.event["error_type"] == "total_byte_budget_exceeded"


def test_read_call_budget(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    ws = SafeWorkspace(tmp_path, max_read_calls=1)
    ws.read_text("a.txt")
    with pytest.raises(PermissionError) as raised:
        ws.read_text("a.txt")
    assert raised.value.event["error_type"] == "read_call_budget_exceeded"
