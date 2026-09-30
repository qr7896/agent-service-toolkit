from pathlib import Path

from evals.e1c_blind_reproducer_v3 import (
    _test_command,
    consistency_witness_candidates,
    django_model_harness_candidates,
    exact_test_candidates,
    repl_transcript_snippets,
)


def test_repl_transcript_extracts_unfenced_commands() -> None:
    statement = """
    >>> from sympy import Matrix
    >>> f = lambda n: Matrix([[n]]).det()
    >>> f(1)
    1
    >>> f(2)
    Traceback (most recent call last):
    TypeError: bad
"""
    snippets = repl_transcript_snippets(statement)
    assert snippets
    assert "from sympy import Matrix" in snippets[0]
    assert "f(2)" in snippets[0]


def test_sympy_consistency_witness_is_executable_assertion() -> None:
    statement = """
is_zero is incorrect.
```
>>> e = -2*I + (1 + I)**2
>>> e.is_zero
False
>>> simplify(e).is_zero
True
```
"""
    candidates = consistency_witness_candidates(statement, "sympy/sympy")
    assert len(candidates) == 1
    source = candidates[0]["content"]
    assert "from sympy import I, simplify" in source
    assert "assert e.is_zero == simplify(e).is_zero" in source
    compile(source, "<witness>", "exec")


def test_django_model_harness_uses_issue_operation() -> None:
    statement = """
class Article(models.Model):
    slug = models.CharField(max_length=255)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["slug"], name="article_slug_unq")
        ]
>>> Article.objects.in_bulk(field_name="slug")
ValueError: not unique
"""
    candidates = django_model_harness_candidates(statement, "django/django")
    assert len(candidates) == 1
    source = candidates[0]["content"]
    assert "app_label = 'blind_repro'" in source
    assert 'Article.objects.in_bulk(field_name="slug")' in source
    compile(source, "<django-harness>", "exec")


def test_exact_test_candidate_selects_matching_node(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    tests = root / "tests"
    tests.mkdir(parents=True)
    (tests / "test_query.py").write_text(
        "def test_unrelated():\n    assert True\n\n"
        "def test_queryset_update():\n    QuerySet = object\n    assert QuerySet\n",
        encoding="utf-8",
    )
    rows = exact_test_candidates("QuerySet update should work", root, "org/repo", limit=2)
    assert rows
    assert rows[0]["nodeid"] == "test_queryset_update"
    assert rows[0]["command"][-1] == "tests/test_query.py::test_queryset_update"


def test_native_test_commands_are_targeted() -> None:
    assert _test_command("sympy/sympy", "sympy/core/tests/test_arit.py", "test_zero") == [
        "python",
        "bin/test",
        "sympy/core/tests/test_arit.py",
        "-k",
        "test_zero",
    ]
    assert _test_command("django/django", "tests/basic/tests.py", "TestBulk::test_slug") == [
        "python",
        "tests/runtests.py",
        "basic.tests.TestBulk.test_slug",
        "--verbosity",
        "0",
    ]
