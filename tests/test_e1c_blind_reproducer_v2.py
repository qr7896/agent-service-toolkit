from evals.e1c_blind_reproducer_v2 import (
    _test_command,
    complete_snippet_from_statement,
    infrastructure_failure,
    issue_probe_candidates,
    reproducer_matches_issue,
)


def test_traceback_assignment_completes_missing_issue_name() -> None:
    snippet = (
        "from sympy.physics.vector import ReferenceFrame, Vector\n"
        "from sympy import symbols\n"
        "sum([N.x, (0 * N.x)])"
    )
    statement = """
3 N = ReferenceFrame('N')
----> 4 sum([N.x, (0 * N.x)])
TypeError: A Vector must be supplied
"""
    completed = complete_snippet_from_statement(snippet, statement)
    assert completed is not None
    assert "N = ReferenceFrame('N')" in completed
    compile(completed, "<completed>", "exec")


def test_issue_candidates_put_completed_repair_sensitive_variant_first() -> None:
    statement = """
```python
from sympy.physics.vector import ReferenceFrame
sum([N.x, 0 * N.x])
```
3 N = ReferenceFrame('N')
TypeError: A Vector must be supplied
"""
    candidates = issue_probe_candidates(statement, "sympy/sympy")
    assert candidates[0]["origin"] == "issue_snippet_completed"
    assert candidates[0]["repair_sensitive"] is True
    assert candidates[0]["content"] != candidates[1]["content"]


def test_infrastructure_failure_is_never_a_reproducer() -> None:
    result = {
        "kind": "original_test",
        "passed": False,
        "timed_out": False,
        "exit_code": 1,
        "tail": "/usr/bin/python: No module named pytest",
    }
    probe = {"matched_symbols": ["solveset"], "repair_sensitive": True}
    assert infrastructure_failure(result) is True
    assert reproducer_matches_issue("solveset should work", result, probe) is False


def test_original_test_failure_requires_issue_symbol_in_failure_output() -> None:
    result = {
        "kind": "original_test",
        "passed": False,
        "timed_out": False,
        "exit_code": 1,
        "tail": "FAILED test_query_update - QuerySet update mismatch",
    }
    assert reproducer_matches_issue(
        "QuerySet update is wrong",
        result,
        {"matched_symbols": ["QuerySet"], "repair_sensitive": True},
    )
    assert not reproducer_matches_issue(
        "QuerySet update is wrong",
        {**result, "tail": "FAILED unrelated test"},
        {"matched_symbols": ["QuerySet"], "repair_sensitive": True},
    )


def test_sympy_uses_repository_native_test_runner() -> None:
    assert _test_command("sympy/sympy", "sympy/core/tests/test_args.py") == [
        "python",
        "bin/test",
        "sympy/core/tests/test_args.py",
    ]
