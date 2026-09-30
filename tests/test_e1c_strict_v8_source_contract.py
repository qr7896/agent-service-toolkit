from pathlib import Path

from evals.e1c_strict_v8_source_contract import (
    evaluate_source_effect,
    evaluate_source_usage,
    extract_source_contracts,
)


def _loc(symbol="check_alpha", path="pkg/checks.py"):
    return {"candidates": [{"path": path, "symbol": symbol, "text": f"def {symbol}(): pass"}]}


def test_extracts_generic_never_used_source_contract() -> None:
    rows = extract_source_contracts("check_alpha is never run?!", _loc())
    assert len(rows) == 1
    assert rows[0]["execution_ready"] is True
    assert rows[0]["witness"]["kind"] == "source_usage"


def test_source_usage_fails_when_symbol_is_only_defined(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "checks.py").write_text("def check_alpha():\n    return 1\n", encoding="utf-8")
    witness = extract_source_contracts("check_alpha is never run", _loc())[0]["witness"]
    result = evaluate_source_usage(tmp_path, witness)
    assert result["passed"] is False
    assert result["definition_count"] == 1


def test_source_usage_passes_when_symbol_is_registered_elsewhere(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "checks.py").write_text("def check_alpha():\n    return 1\n", encoding="utf-8")
    (package / "registry.py").write_text("from .checks import check_alpha\nCHECKS = register(check_alpha)\n", encoding="utf-8")
    witness = extract_source_contracts("check_alpha is never run", _loc())[0]["witness"]
    result = evaluate_source_usage(tmp_path, witness)
    assert result["passed"] is True
    assert result["external_registration_count"] >= 1


def test_extracts_and_evaluates_generic_clear_effect(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "checks.py").write_text(
        "def unregister():\n    registry.pop('x', None)\n",
        encoding="utf-8",
    )
    rows = extract_source_contracts(
        "unregister() should clear the lookup cache.",
        _loc(symbol="unregister"),
    )
    effect = [row for row in rows if row["witness"]["kind"] == "source_effect"]
    assert len(effect) == 1
    before = evaluate_source_effect(tmp_path, effect[0]["witness"])
    assert before["passed"] is False
    (package / "checks.py").write_text(
        "def unregister():\n    registry.pop('x', None)\n    clear_lookup_cache()\n",
        encoding="utf-8",
    )
    after = evaluate_source_effect(tmp_path, effect[0]["witness"])
    assert after["passed"] is True


def test_source_effect_ignores_nested_function_clear_calls(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "checks.py").write_text(
        "def unregister():\n"
        "    def helper():\n"
        "        clear_lookup_cache()\n"
        "    return helper\n",
        encoding="utf-8",
    )
    witness = extract_source_contracts(
        "unregister() should clear the lookup cache.",
        _loc(symbol="unregister"),
    )[0]["witness"]
    result = evaluate_source_effect(tmp_path, witness)
    assert result["passed"] is False


def test_source_usage_does_not_count_import_only_as_registration(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "checks.py").write_text("def check_alpha():\n    return 1\n", encoding="utf-8")
    (package / "registry.py").write_text("from .checks import check_alpha\n", encoding="utf-8")
    witness = extract_source_contracts("check_alpha is never run", _loc())[0]["witness"]
    result = evaluate_source_usage(tmp_path, witness)
    assert result["passed"] is False


def test_source_usage_ignores_test_tree_calls(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    tests = tmp_path / "tests"
    tests.mkdir()
    (package / "checks.py").write_text("def check_alpha():\n    return 1\n", encoding="utf-8")
    (tests / "test_checks.py").write_text(
        "from pkg.checks import check_alpha\ncheck_alpha()\n",
        encoding="utf-8",
    )
    witness = extract_source_contracts("check_alpha is never run", _loc())[0]["witness"]
    result = evaluate_source_usage(tmp_path, witness)
    assert result["passed"] is False
