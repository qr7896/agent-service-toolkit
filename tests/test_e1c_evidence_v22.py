from evals.e1c_evidence_v22 import excerpts


def test_dotted_method_beats_documentation_mentions(tmp_path):
    (tmp_path / "docs.py").write_text("Header fromstring " * 40, encoding="utf-8")
    (tmp_path / "header.py").write_text(
        "class Header:\n    def fromstring(self, value):\n        return value\n",
        encoding="utf-8",
    )
    found = excerpts("Header.fromstring does not accept Python 3 bytes", tmp_path)
    assert found[0]["path"] == "header.py"
    assert "def fromstring" in found[0]["text"]


def test_named_method_beats_generic_title_file(tmp_path):
    (tmp_path / "transaction.py").write_text("transaction " * 80, encoding="utf-8")
    (tmp_path / "options.py").write_text(
        "def changelist_view(self):\n    return None\n", encoding="utf-8"
    )
    found = excerpts(
        "Add transaction handling to Changelist list_editable processing.\n"
        "The changelist_view is missing a transaction.", tmp_path
    )
    assert found[0]["path"] == "options.py"
