from evals.serbench_upstream_resolver import resolve


def test_resolve_explicit(tmp_path):
    (tmp_path / "src" / "serbench").mkdir(parents=True)
    (tmp_path / "README.md").write_text("x")
    (tmp_path / "pyproject.toml").write_text("x")
    assert resolve(tmp_path)["ready"]
