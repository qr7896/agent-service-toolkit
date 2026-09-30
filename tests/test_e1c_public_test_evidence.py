from evals.e1c_public_test_evidence import added_test_lines


def test_only_public_test_additions_and_limits():
    patch = """diff --git a/pkg/source.py b/pkg/source.py
--- a/pkg/source.py
+++ b/pkg/source.py
@@ -1 +1 @@
-old
+secret_source
diff --git a/tests/test_feature.py b/tests/test_feature.py
--- a/tests/test_feature.py
+++ b/tests/test_feature.py
@@ -1 +1 @@
-old_test
+assert result == 42
+assert other is None
"""
    excerpt = added_test_lines(patch, max_chars=100, max_lines=1)
    assert excerpt == "tests/test_feature.py: assert result == 42"
    assert "secret_source" not in excerpt


def test_invalid_limit():
    import pytest

    with pytest.raises(ValueError):
        added_test_lines("", max_chars=0)
