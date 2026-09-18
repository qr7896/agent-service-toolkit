from evals.codegraph_adapter import CodeGraphAdapter
from evals.safe_workspace import SafeWorkspace


def setup_repo(tmp_path):
    (tmp_path / "a.py").write_text(
        chr(10).join(
            ["import os", "from pkg.mod import helper", "", "def target(x):", "    return x"]
        )
        + chr(10)
    )
    (tmp_path / "b.py").write_text(
        chr(10).join(["from a import target", "", "def caller():", "    return target(1)"])
        + chr(10)
    )
    return CodeGraphAdapter(SafeWorkspace(tmp_path))


def test_symbols(tmp_path):
    cg = setup_repo(tmp_path)
    hits = cg.symbols("target")
    assert len(hits) == 1 and hits[0].path == "a.py" and hits[0].symbol == "target"
    assert (
        hits[0].relation_type == "definition" and hits[0].depth == 0 and hits[0].origin == "target"
    )


def test_imports(tmp_path):
    cg = setup_repo(tmp_path)
    names = {x.content for x in cg.imports("target")}
    assert "a.target" in names


def test_callers(tmp_path):
    cg = setup_repo(tmp_path)
    hits = cg.callers("target")
    assert len(hits) == 1 and hits[0].path == "b.py"


def test_syntax_error_isolated(tmp_path):
    cg = setup_repo(tmp_path)
    (tmp_path / "broken.py").write_text("def broken(")
    assert cg.symbols("target")[0].path == "a.py"


def test_neighbors_deduplicate(tmp_path):
    cg = setup_repo(tmp_path)
    hits = cg.neighbors("target")
    assert any(x.path == "a.py" for x in hits)
    assert any(x.path == "b.py" for x in hits)
    assert len({x.key for x in hits}) == len(hits)


def test_traverse_respects_node_budget(tmp_path):
    cg = setup_repo(tmp_path)
    hits = cg.traverse("target", max_depth=2, max_nodes=2)
    assert len(hits) <= 2
    assert all(x.origin == "target" and x.depth is not None for x in hits)
    assert {x.relation_type for x in hits} <= {"definition", "caller", "import"}


def test_traverse_rejects_invalid_budget(tmp_path):
    import pytest

    cg = setup_repo(tmp_path)
    with pytest.raises(ValueError):
        cg.traverse("target", max_depth=-1)
    with pytest.raises(ValueError):
        cg.traverse("target", max_nodes=0)
