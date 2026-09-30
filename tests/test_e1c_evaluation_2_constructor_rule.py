import pytest

from evals.e1c_evaluation_2_constructor_rule import source_from_public_issue


def test_boolean_constructor_rule_uses_only_exact_public_request_and_path():
    quote = "expose `enabled` in `Widget.__init__()`, default `False`"
    issue = "Use `acme.widgets.Widget` and " + quote
    source = source_from_public_issue(issue, quote)
    assert "from acme.widgets import Widget" in source
    assert "Widget(enabled=True)" in source
    assert "assert baseline.enabled is False" in source
    with pytest.raises(ValueError, match="exact Boolean constructor"):
        source_from_public_issue(issue, quote.replace("False", "True"))
    with pytest.raises(ValueError, match="one public import path"):
        source_from_public_issue(quote, quote)
