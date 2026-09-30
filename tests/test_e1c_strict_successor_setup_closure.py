from evals.e1c_strict_successor_setup_closure import (
    close_with_public_assignments,
    extract_candidates,
    free_names,
)


def test_free_names_respects_local_bindings_imports_and_builtins():
    src = "import math\nx = math.sqrt(4)\nprint(x)\n"
    assert free_names(src) == ()


def test_free_names_reports_unresolved_setup():
    src = "qs = Number.objects.filter(pk=OuterRef('pk'))\nprint(qs)\n"
    assert free_names(src) == ("Number", "OuterRef")


def test_extracts_fenced_python_candidate():
    text = "Example:\n\n```python\nimport math\nx = math.sqrt(4)\nprint(x)\n```\n"
    rows = extract_candidates(text)
    assert len(rows) == 1
    assert rows[0].closed is True
    assert rows[0].origin == "fenced"
    assert rows[0].behavioral is True


def test_paragraph_fallback_is_fail_closed_on_narrative():
    text = "Description\n\nvalue = missing_name()\nprint(value)\n"
    rows = extract_candidates(text)
    assert len(rows) == 1
    assert rows[0].closed is False
    assert rows[0].free_names == ("missing_name",)


def test_public_traceback_assignment_can_close_unresolved_local_setup():
    text = """```python
from package import Factory
consume(N.value)
```
Traceback:
      3 N = Factory('N')
----> 4 consume(N.value)
"""
    candidate = extract_candidates(text)[0]
    assert candidate.free_names == ("N", "consume")
    # Only N is recoverable from public assignment; unknown consume remains fail-closed.
    closed = close_with_public_assignments(text, candidate)
    assert closed.free_names == ("consume",)
    assert closed.closed is False
    assert closed.recovered_names == ("N",)


def test_public_assignment_closes_when_other_names_are_imported():
    text = """```python
from package import Factory, consume
consume(N.value)
```
Traceback:
      3 N = Factory('N')
----> 4 consume(N.value)
"""
    candidate = extract_candidates(text)[0]
    closed = close_with_public_assignments(text, candidate)
    assert closed.closed is True
    assert closed.free_names == ()
    assert closed.behavioral is True
    assert closed.recovered_names == ("N",)


def test_plain_configuration_is_not_behavioral():
    rows = extract_candidates("```python\noption = 'documented'\n```")
    assert rows[0].closed is True
    assert rows[0].behavioral is False
