from evals.e1c_blind_reproducer_v4 import (
    django_inline_test_witness_candidates,
    django_migration_order_witness_candidates,
    django_reverse_prefetch_slice_witness_candidates,
)


def test_reverse_prefetch_slice_witness_builds_asserting_harness() -> None:
    statement = """Category.objects.prefetch_related(Prefetch(
        'post_set',
        queryset=Post.objects.all()[:3],
        to_attr='example_posts',
    ))
AssertionError: Cannot filter a query once a slice has been taken."""
    rows = django_reverse_prefetch_slice_witness_candidates(statement, "django/django")
    assert len(rows) == 1
    source = rows[0]["content"]
    assert "models.ForeignKey(Category" in source
    assert "list(queryset)" in source
    assert "assert len(rows[0].example_posts) == 3" in source
    assert rows[0]["expected_failure_fragment"] == "Cannot filter a query once a slice has been taken."
    compile(source, "<prefetch>", "exec")


def test_inline_issue_test_becomes_standalone_query_assertion() -> None:
    statement = """
class User(models.Model):
    email = models.EmailField()
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
def test_only_related_queryset(self):
    user = User.objects.create(email="a@example.com")
    Profile.objects.create(user=user)
    with self.assertNumQueries(0):
        self.assertEqual(user.email, "a@example.com")
"""
    rows = django_inline_test_witness_candidates(statement, "django/django")
    assert len(rows) == 1
    source = rows[0]["content"]
    assert "CaptureQueriesContext" in source
    assert "from django.db.models import Prefetch" not in source
    assert "_BlindAssertions" in source
    assert "_blind_test_only_related_queryset(_BlindAssertions())" in source
    compile(source, "<inline>", "exec")


def test_migration_order_witness_asserts_remove_before_create() -> None:
    statement = """
from django.db import models
class Readable(models.Model):
    title = models.CharField(max_length=200)
And change to this:
from django.db import models
class Readable(models.Model):
    pass
class Book(Readable):
    title = models.CharField(max_length=200)
The migration generates with CreateModel for Book, then RemoveField for Readable.title.
Reversing the order of the migration operations makes it pass. The auto-detector should be able to use this order.
"""
    rows = django_migration_order_witness_candidates(statement, "django/django")
    assert len(rows) == 1
    source = rows[0]["content"]
    assert "MigrationAutodetector" in source
    assert "assert remove_index < create_index" in source
    compile(source, "<migration>", "exec")
