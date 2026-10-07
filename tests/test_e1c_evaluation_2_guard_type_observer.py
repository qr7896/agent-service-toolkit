import ast

import pytest

from evals.e1c_evaluation_2_guard_type_observer import build_driver


def site(**changes):
    return {"path": "core.py", "line": 3, "variable": "labels", "source_sha256": "a" * 64, **changes}


def test_driver_only_runs_owned_probe_and_emits_types_not_values():
    source, marker = build_driver("b" * 64, [site()], "c" * 32)
    ast.parse(source)
    assert "/e1c2_model_probe.py" in source and marker in source
    assert "argument_values_emitted" in source and "sys.settrace(None)" in source
    assert "getattr(" not in source and "repr(" not in source and "bool(frame" not in source


@pytest.mark.parametrize("bad", [site(path="tests/answer.py"), site(path="../secret.py"), site(line=True),
                                  site(variable="__dict__"), site(variable="x; eval(code)"), site(shell="pytest")])
def test_unknown_paths_fields_and_capabilities_rejected(bad):
    with pytest.raises(Exception):
        build_driver("b" * 64, [bad], "c" * 32)
