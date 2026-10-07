import subprocess

import evals.v3_pilot_runner as runner
from evals.v3_pilot_runner import (
    MAX_CALLS_PER_TASK,
    TASK_TOKEN_CEILING,
    TASKS,
    TOTAL_TOKEN_CEILING,
    _attribute_grade,
    _run,
)


def test_snapshot_excludes_only_root_live_checkpoint_database():
    names = ["checkpoints.db", "checkpoints.db-wal", "checkpoints.db-shm", "source.py", "fixture.db"]
    assert runner._ignore(str(runner.ROOT), names) == {"checkpoints.db", "checkpoints.db-wal", "checkpoints.db-shm"}
    assert runner._ignore(str(runner.ROOT / "tests" / "fixtures"), names) == set()


def test_v3_pilot_is_small_nonsealed_and_budgeted():
    assert len(TASKS) == 3
    assert len({task.instance_id for task in TASKS}) == 3
    assert all(task.base_commit != task.fix_commit for task in TASKS)
    assert TOTAL_TOKEN_CEILING == len(TASKS) * TASK_TOKEN_CEILING == 30_000
    assert MAX_CALLS_PER_TASK == 4


def test_grade_failure_attribution_separates_candidate_and_infrastructure():
    assert _attribute_grade({"passed": True}) == "none"
    assert _attribute_grade({"passed": False, "timed_out": True, "tests_started": False}) == "grader_bootstrap_timeout"
    assert _attribute_grade({"passed": False, "timed_out": True, "tests_started": True}) == "candidate_timeout"
    assert _attribute_grade({"passed": False, "stdout": "FAILED x.py::test_x - AssertionError", "stderr": ""}) == "candidate_assertion_failure"
    assert _attribute_grade({"passed": False, "stdout": "", "stderr": "Traceback (most recent call last)"}) == "candidate_exception"
    assert _attribute_grade({"passed": False, "stdout": "exit 1", "stderr": ""}) == "verification_failure"


def test_run_attributes_timeout_without_raising(monkeypatch, tmp_path):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 1, output="collected 1 item\nx.py::test_x ")

    monkeypatch.setattr(runner.subprocess, "run", timeout)
    grade = _run(["pytest", "-q"], tmp_path, timeout=1)
    assert grade["exit_code"] == 124
    assert grade["timed_out"] is True
    assert grade["tests_started"] is True
    assert _attribute_grade(grade) == "candidate_timeout"
