import ast
import hashlib

import pytest

from evals.e1c_evaluation_2_contract_recovery import tree_sha
from evals.e1c_evaluation_2_runtime_frontier_zero import shift_from_control


def inputs(control_action="Api()", target_action="Broken()"):
    payload = {"setup_source": "from core import Api, Broken\nseed = 2\nbroken = Broken()",
               "control_action": control_action, "target_action": target_action,
               "issue_quote": "a public software issue", "expected_quote": "should complete", "oracle": "call_completes", "assertion": ""}
    source = payload["setup_source"] + "\n" + control_action + "\n"
    sha = hashlib.sha256(source.encode()).hexdigest()
    candidate = {"source": source, "probe_sha256": sha}
    execution = {"probe_sha256": sha, "runs": [{"returncode": 1, "timed_out": False,
                 "log_tail": 'Traceback:\n  File "/e1c2_probe.py", line 3, in <module>\nValueError: reported defect'}]}
    return payload, candidate, [execution, execution]


def test_shift_preserves_whole_target_and_control_and_oracle():
    original, control, executions = inputs()
    result, proof = shift_from_control(original, control, executions)
    assert proof["compiled"] and "broken =" not in result["setup_source"]
    assert tree_sha(ast.parse(original["setup_source"] + "\n" + original["target_action"])) == tree_sha(ast.parse(result["setup_source"] + "\n" + result["target_action"]))
    assert all(result[k] == original[k] for k in original if k not in {"setup_source", "target_action"})
    assert proof["untrusted_trace_not_semantic_proof"]


def test_shared_removed_binding_keeps_unknown_not_fabricated_control():
    original, control, executions = inputs("broken.run()")
    result, proof = shift_from_control(original, control, executions)
    assert result == original and not proof["compiled"]
    assert proof["status"] == "normal_control_depends_on_moved_bindings"


@pytest.mark.parametrize("line", [1, 2, 4, 5])
def test_non_call_setup_and_control_action_frames_not_relabelled(line):
    original, control, executions = inputs()
    executions[0]["runs"][0]["log_tail"] = f'Traceback:\n  File "/e1c2_probe.py", line {line}, in <module>\nValueError: failure'
    assert not shift_from_control(original, control, executions)[1]["compiled"]


@pytest.mark.parametrize("code", [0, 90, 125, 126, 127, None])
def test_success_or_infrastructure_never_justifies_shift(code):
    original, control, executions = inputs()
    executions[0]["runs"][0]["returncode"] = code
    if code in {125, 126, 127}:
        with pytest.raises(ValueError):
            shift_from_control(original, control, executions)
    else:
        assert not shift_from_control(original, control, executions)[1]["compiled"]


def test_source_binding_and_timeout_fail_closed():
    original, control, executions = inputs()
    executions[0]["probe_sha256"] = "different"
    with pytest.raises(ValueError):
        shift_from_control(original, control, executions)
    executions[0]["probe_sha256"] = control["probe_sha256"]
    executions[0]["runs"][0]["timed_out"] = True
    assert not shift_from_control(original, control, executions)[1]["compiled"]
