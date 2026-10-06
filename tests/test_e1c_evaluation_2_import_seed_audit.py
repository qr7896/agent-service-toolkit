from evals.e1c_evaluation_2_import_seed_audit import import_prefix_seeds, import_windows


def test_assertion_values_and_target_names_do_not_seed_routing():
    a = "```python\nfrom pkg import Encode\nassert SecretAnswer() == 42\nfrom pkg import Hidden\n```"
    b = "```python\nfrom pkg import Encode\nassert DifferentOracle() == 900\nfrom pkg import Hidden\n```"
    assert import_prefix_seeds(a) == import_prefix_seeds(b) == [
        {"module": "pkg", "symbol": "Encode", "block": 1, "origin": "public_import_prefix_only"}]
    assert "SecretAnswer" not in str(import_prefix_seeds(a)) and "Hidden" not in str(import_prefix_seeds(a))


def test_forbidden_test_wildcard_and_nested_imports_do_not_seed():
    for source in ("import pytest\nfrom pkg import F", "from pkg import *\nfrom pkg import F",
                   "from pkg import assert_answer\nfrom pkg import F", "from pkg import F as assert_answer",
                   "def f():\n    from pkg import F", "from os import system\nfrom pkg import F"):
        assert import_prefix_seeds(f"```python\n{source}\n```") == []


def test_reexports_resolve_without_importing_package_or_oracle(tmp_path):
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("raise RuntimeError('must not execute')\nfrom .ops import Convert, Print\n", encoding="utf-8")
    (package / "ops.py").write_text("class Convert:\n    pass\n\ndef Print(x):\n    return str(x)\n", encoding="utf-8")
    statement = "```python\nfrom pkg import Convert, Print\nassert PrivateOracle() == 'not visible'\n```"
    result = import_windows(statement, tmp_path)
    assert [(row["path"], row["symbol"], row["depth"]) for row in result] == [
        ("pkg/ops.py", "Convert", 1), ("pkg/ops.py", "Print", 1)]
    assert all(row["relation_type"] == "definition" and row["source_sha256"] for row in result)
    assert all("PrivateOracle" not in str(row) and "not visible" not in str(row) for row in result)


def test_missing_or_ambiguous_production_origin_does_not_guess(tmp_path):
    assert import_windows("```python\nfrom external import API\n```", tmp_path) == []
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg.py").write_text("def F():\n    pass\n", encoding="utf-8")
    (tmp_path / "pkg/__init__.py").write_text("def F():\n    pass\n", encoding="utf-8")
    assert import_windows("```python\nfrom pkg import F\n```", tmp_path) == []
