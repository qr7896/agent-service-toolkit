from pathlib import Path

from evals.e1c_blind_evidence import (
    ast_windows,
    discover_original_test_probes,
    extract_contract,
    freeze_blind_evidence,
    lexical_windows,
)


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "pkg").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "pkg" / "parser.py").write_text(
        "def parse_value(value):\n    return value.strip()\n", encoding="utf-8"
    )
    (root / "tests" / "test_parser.py").write_text(
        "from pkg.parser import parse_value\n\ndef test_parse_value():\n    assert parse_value(' x ') == 'x'\n",
        encoding="utf-8",
    )
    return root


def test_contract_and_ast_windows_are_issue_base_only(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    statement = "parse_value should preserve empty values instead of failing."
    contract = extract_contract(statement)
    assert "parse_value" in contract["symbols"]
    windows = ast_windows(statement, root)
    assert windows[0]["path"] == "pkg/parser.py"
    assert windows[0]["origin"] == "issue_ast_definition"
    assert all("tests/" not in item["path"] for item in windows)


def test_original_test_probe_or_no_reproducer_is_observable(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    found = discover_original_test_probes("parse_value should preserve values.", root)
    assert found["status"] == "existing_test_probe"
    assert found["probes"][0]["path"] == "tests/test_parser.py"
    missing = discover_original_test_probes("unrelated_symbol should change.", root)
    assert missing["status"] == "no_reproducer"
    assert missing["probes"] == []


def test_frozen_evidence_is_deterministic(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    statement = "parse_value should preserve empty values."
    first = freeze_blind_evidence(statement, root)
    second = freeze_blind_evidence(statement, root)
    assert first["evidence_sha256"] == second["evidence_sha256"]
    assert first["reproducer"]["oracle_used"] is False


def test_exact_public_cli_option_outweighs_incidental_words(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "pkg" / "deprecated.py").write_text(
        "# strict deprecation warnings for another option\n", encoding="utf-8"
    )
    (root / "pkg" / "main.py").write_text(
        'options.addoption("--strict")\n', encoding="utf-8"
    )
    (root / "pkg" / "config.py").write_text(
        'options.addoption("--strict-config")\n', encoding="utf-8"
    )
    windows = lexical_windows("Deprecate `--strict`", root)
    assert windows[0]["path"] == "pkg/main.py"
    assert '"--strict"' in windows[0]["text"]
