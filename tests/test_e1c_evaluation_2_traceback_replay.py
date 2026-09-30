import pytest

from evals.e1c_evaluation_2_traceback_replay import public_exception_quote


def test_public_exception_quote_requires_one_verbatim_exception_line():
    issue = "Traceback:\n    AttributeError: 'List' object has no attribute 'opts'\n"
    assert public_exception_quote(issue) == "AttributeError: 'List' object has no attribute 'opts'"
    with pytest.raises(ValueError, match="found 0"):
        public_exception_quote("No explicit exception")
    with pytest.raises(ValueError, match="found 2"):
        public_exception_quote(issue + "TypeError: another failure\n")
