from pathlib import Path

from evals.e1c_strict_v5_runner import prepare_fixture


def test_prepare_fixture_writes_only_projected_bundle(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "module.py").write_text(
        "def calculate(value):\n    return value\n",
        encoding="utf-8",
    )
    statement = """calculate should return the normalized value.
def test_secret():
    assert calculate(1) == 99
The current behavior is incorrect.
"""
    sentinel = "assert calculate(1) == 99"
    result = prepare_fixture(
        instance_id="fixture",
        statement=statement,
        workspace=workspace,
        base_commit="c" * 40,
        output_dir=tmp_path / "out",
        forbidden_values=(sentinel,),
    )
    assert result["status"] == "prepared"
    text = (tmp_path / "out" / "bundle.json").read_text(encoding="utf-8")
    assert sentinel not in text
    assert "def test_secret" not in text
    assert "module.py" in text
