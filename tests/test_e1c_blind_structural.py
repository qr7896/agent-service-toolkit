from pathlib import Path

from evals.e1c_blind_evidence import structural_windows


def test_structural_windows_include_definition_and_caller(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "pkg").mkdir(parents=True)
    (root / "pkg" / "api.py").write_text(
        "def target_symbol(value):\n    return value\n\n"
        "def wrapper(value):\n    return target_symbol(value)\n",
        encoding="utf-8",
    )
    windows = structural_windows(
        "target_symbol should preserve values instead of failing.",
        root,
        limit=4,
    )
    origins = {(item["symbol"], item["origin"], item["depth"]) for item in windows}
    assert ("target_symbol", "issue_ast_definition", 0) in origins
    assert ("wrapper", "ast_caller", 1) in origins
