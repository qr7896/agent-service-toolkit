import pytest

from evals.e1c_dev_missing_import import add_import


def test_add_import_after_docstring_and_future():
    text = '"""module"""\nfrom __future__ import annotations\nfrom collections import Counter\n'
    assert add_import(text, "json") == (
        '"""module"""\nfrom __future__ import annotations\nimport json\nfrom collections import Counter\n')
    with pytest.raises(ValueError, match="already imported"):
        add_import("import json\n", "json")
