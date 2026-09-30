from pathlib import Path

from evals.e1c_blind_runtime import (
    build_runtime_view,
    expected_exception_names,
    freeze_probe_plan,
    issue_python_snippets,
    repair_probe_context,
    reproducer_matches_issue,
)


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "pkg").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "pkg" / "vector.py").write_text(
        "def add_zero(value):\n    return value\n", encoding="utf-8"
    )
    (root / "tests" / "test_vector.py").write_text(
        "from pkg.vector import add_zero\n\ndef test_add_zero():\n    assert add_zero(1) == 1\n",
        encoding="utf-8",
    )
    return root


def test_issue_python_snippets_ignores_non_python_and_traceback() -> None:
    statement = """Example
```julia
In [1]: broken()
```
```python
>>> from pkg.vector import add_zero
>>> add_zero(1)
```
"""
    assert issue_python_snippets(statement) == [
        "from pkg.vector import add_zero\nadd_zero(1)"
    ]


def test_issue_exception_match_rejects_wrong_failure_type() -> None:
    statement = "Operation raises TypeError instead of returning normally."
    assert expected_exception_names(statement) == ("TypeError",)
    wrong = {
        "kind": "issue_snippet",
        "passed": False,
        "timed_out": False,
        "exit_code": 1,
        "tail": "NameError: missing variable",
    }
    right = {**wrong, "tail": "TypeError: expected failure"}
    assert reproducer_matches_issue(statement, wrong) is False
    assert reproducer_matches_issue(statement, right) is True


def test_probe_plan_uses_issue_snippet_then_original_test(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    statement = """add_zero should preserve zero.
```python
from pkg.vector import add_zero
assert add_zero(0) == 0
```
"""
    row = {
        "instance_id": "repo__issue-1",
        "repo": "org/repo",
        "base_commit": "a" * 40,
        "image": "swebench/example:latest",
    }
    view = build_runtime_view(row["instance_id"], statement, root)
    plan = freeze_probe_plan(row, view)
    assert plan["probes"][0]["kind"] == "issue_snippet"
    assert plan["probes"][0]["role"] == "reproducer"
    assert plan["probes"][1]["kind"] == "original_test"
    assert plan["probes"][1]["role"] == "audit"


def test_repair_probe_context_hides_audit_output() -> None:
    prepatch = {
        "reproducer_status": "reproduced_failure",
        "results": [
            {
                "role": "reproducer",
                "kind": "issue_snippet",
                "exit_code": 1,
                "tail": "TypeError: bad",
                "log_sha256": "abc",
            },
            {
                "role": "audit",
                "kind": "original_test",
                "exit_code": 0,
                "tail": "secret audit output",
                "log_sha256": "def",
            },
        ],
    }
    context = repair_probe_context(prepatch)
    assert context["tail"] == "TypeError: bad"
    assert "secret audit output" not in str(context)
