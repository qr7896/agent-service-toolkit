from evals.v3_pilot_runner import (
    MAX_CALLS_PER_TASK,
    TASK_TOKEN_CEILING,
    TASKS,
    TOTAL_TOKEN_CEILING,
)


def test_v3_pilot_is_small_nonsealed_and_budgeted():
    assert len(TASKS) == 3
    assert len({task.instance_id for task in TASKS}) == 3
    assert all(task.base_commit != task.fix_commit for task in TASKS)
    assert TOTAL_TOKEN_CEILING == len(TASKS) * TASK_TOKEN_CEILING == 30_000
    assert MAX_CALLS_PER_TASK == 4
