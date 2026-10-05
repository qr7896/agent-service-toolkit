import hashlib

from evals.e1c_evaluation_2_source_contract import optional_import, rephase_setup


def test_optional_dependency_requirement_survives_window_repacking(tmp_path):
    package = tmp_path / "pkg"
    package.mkdir()
    code = "import sampledep\ndef api(value):\n    return value\n"
    (package / "core.py").write_bytes(code.encode())
    frozen = {"issue": "With `python-sampledep` not installed, api should work.", "candidate_paths": ["pkg/core.py"],
              "windows": [{"path": "pkg/core.py", "text": "def api(value): return value",
                           "source_sha256": hashlib.sha256(code.encode()).hexdigest()}]}
    value = optional_import(frozen, tmp_path)
    assert value["missing_optional_import"] == "sampledep"
    assert value["evidence"] == [{"path": "pkg/core.py", "line": 1, "module": "sampledep"}]


def test_target_constructor_frontier_keeps_expected_behavior_and_control_setup(tmp_path):
    package = tmp_path / "pkg"
    package.mkdir()
    code = "class Engine:\n    def __init__(self, count=1): self.count = count\n    def run(self): return self.count\n"
    (package / "core.py").write_bytes(code.encode())
    frozen = {"candidate_paths": ["pkg/core.py"], "windows": [{"path": "pkg/core.py", "source_sha256": hashlib.sha256(code.encode()).hexdigest()}]}
    payload = {"setup_source": "from pkg.core import Engine\nvalue = 1\ne = Engine(new_option=True)\ne.count = 2",
               "target_action": "e.run()", "control_action": "Engine().run()", "expected_quote": "support the new option"}
    changed, frontier = rephase_setup(payload, frozen, tmp_path)
    assert changed["setup_source"] == "from pkg.core import Engine\nvalue = 1"
    assert changed["target_action"].endswith("e.run()")
    assert "Engine(new_option=True)" in changed["target_action"]
    assert changed["expected_quote"] == payload["expected_quote"] and changed["control_action"] == payload["control_action"]
    assert frontier["source_proven_unsupported_keywords"] == ["new_option"]
