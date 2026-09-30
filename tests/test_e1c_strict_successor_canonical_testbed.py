from evals.e1c_strict_successor_canonical_testbed import CANONICAL_TESTBED_PYTHON


def test_canonical_testbed_python_is_fixed_not_task_conditioned():
    assert CANONICAL_TESTBED_PYTHON == "/opt/miniconda3/envs/testbed/bin/python"
    assert "sympy" not in CANONICAL_TESTBED_PYTHON
    assert "django" not in CANONICAL_TESTBED_PYTHON
