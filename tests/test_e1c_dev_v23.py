import pytest

from evals.e1c_dev_v23 import SYSTEM, _fit, _inspect, _reserve


def test_inspection_reads_only_selected_source_symbol(tmp_path):
    source = tmp_path / "pkg" / "logic.py"
    source.parent.mkdir()
    source.write_text("def target(value):\n    return value\n", encoding="utf-8")
    item = _inspect(tmp_path, ["pkg/logic.py"], {"path": "pkg/logic.py", "symbol": "target"})
    assert item["path"] == "pkg/logic.py" and "def target" in item["text"]
    with pytest.raises(ValueError):
        _inspect(tmp_path, ["pkg/logic.py"], {"path": "tests/test_logic.py", "symbol": "target"})


def test_first_payload_fits_without_dropping_both_excerpts():
    value = {"task": "Fix target", "excerpts": [
        {"path": "a.py", "text": "def target(): pass"},
        {"path": "b.py", "text": "def helper(): pass"}], "candidate_paths": ["a.py", "b.py"]}
    fitted = _fit(value, SYSTEM, multiplier=1.25, available=7000)
    assert len(fitted["excerpts"]) == 2
    assert _reserve(fitted, SYSTEM, multiplier=1.25) <= 7000
