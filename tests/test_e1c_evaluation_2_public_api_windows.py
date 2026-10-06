from evals.e1c_evaluation_2_issue_fixture_facts import extract_facts
from evals.e1c_evaluation_2_public_api_windows import terminal_windows


def test_reexport_owner_and_terminal_method_win_over_unrelated_same_name(tmp_path):
    package = tmp_path / "demo"
    package.mkdir()
    (package / "__init__.py").write_bytes(b"from .geometry import Anchor\n")
    (package / "geometry.py").write_bytes(b'class Anchor:\n    def velocity(self, frame):\n        """doc"""\n        return frame\n')
    (package / "unrelated.py").write_bytes(b"class Anchor:\n    def velocity(self, frame): return 999\n")
    text = "Velocity should work.\n```python\nfrom demo import Anchor\nA = Anchor()\nA.velocity(F)\n```"
    rows = terminal_windows(extract_facts(text), tmp_path)
    assert len(rows) == 1 and rows[0]["path"] == "demo/geometry.py"
    assert rows[0]["symbol"] == "velocity" and rows[0]["owner"] == "Anchor"
    assert "return frame" in rows[0]["text"] and '"""doc"""' not in rows[0]["text"]


def test_inherited_assigned_terminal_fit_is_resolved_without_import_execution(tmp_path):
    package = tmp_path / "demo"
    package.mkdir()
    (package / "__init__.py").write_bytes(b"raise RuntimeError('must never import')\nfrom .core import Estimator\n")
    (package / "core.py").write_bytes(b"class Base:\n    def fit(self, X, y): return self\nclass Estimator(Base):\n    pass\n")
    text = "Fit should work.\n```python\nfrom demo import Estimator\nest = Estimator().fit(X, y)\n```"
    rows = terminal_windows(extract_facts(text), tmp_path)
    assert rows[0]["relation_type"] == "inherited_method" and rows[0]["owner"] == "Base"
    assert rows[0]["path"] == "demo/core.py"
    assert rows[0]["depth"] == 2
    assert rows[0]["origin_seed"] == {"module": "demo", "symbol": "Estimator"}
