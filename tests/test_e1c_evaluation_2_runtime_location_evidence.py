import pytest

from evals.e1c_evaluation_2_runtime_location_evidence import production_locations


def diagnostic(path="../../testbed/src/pkg/core.py", line=239):
    return {"generated_case": "/tmp/e1c2-generated-only-owned/generated_case.py", "results": {
        "control": {"locations": [{"path": "generated_case.py", "line": 3}]},
        "target": {"locations": [{"path": path, "line": line}]}}}


def test_only_production_frame_becomes_evidence_not_own_test_file():
    rows = production_locations(diagnostic())
    assert rows == [{"path": "src/pkg/core.py", "line": 239, "report": "target", "origin": "owned_native_runtime_report"}]


@pytest.mark.parametrize("path", ["../../testbed/tests/answer.py", "../../testbed/.codex/gold.patch",
                                   "../../../etc/passwd", "C:\\private\\answer.py", "../../testbed/.git/source.py",
                                   "../../testbed/docs/source.py", "../../testbed/conftest.py"])
def test_oracle_and_workspace_escape_frames_fail_closed(path):
    with pytest.raises(Exception):
        production_locations(diagnostic(path))


@pytest.mark.parametrize("line", [True, 0, -1, 1000001])
def test_location_requires_bounded_integer_line(line):
    with pytest.raises(ValueError):
        production_locations(diagnostic(line=line))


def test_forged_generated_fixture_root_is_not_an_owned_diagnostic():
    value = diagnostic()
    value["generated_case"] = "/tmp/e1c2-generated-only-../../testbed/generated_case.py"
    with pytest.raises(ValueError, match="owned_generated_fixture"):
        production_locations(value)
