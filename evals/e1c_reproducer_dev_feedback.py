"""Fail-closed classification of proposed issue-reproduction probe outcomes."""

from __future__ import annotations

import re

from evals.e1c_strict_successor_expected_failure import FailureContract, classify_failure

_SETUP_ERROR = re.compile(
    r"\b(?:SyntaxError|IndentationError|ModuleNotFoundError|ImportError|NameError)\b"
    r"|fixture ['\"]?.+?['\"]? not found|ERROR collecting",
    re.IGNORECASE,
)
_ASSERTION_ERROR = re.compile(r"\bAssertionError\b|^E\s+assert\b", re.MULTILINE)


def classify_probe_outcome(
    *,
    returncode: int | None,
    timed_out: bool,
    stdout: str,
    stderr: str,
    public_exception: FailureContract | None = None,
) -> dict:
    """A failing process is a candidate, never automatically a trusted reproducer."""
    log = stdout[-8000:] + "\n" + stderr[-8000:]
    if timed_out:
        reason = "timeout"
    elif returncode is None:
        reason = "not_executed"
    elif returncode == 0:
        reason = "no_prepatch_failure"
    elif _SETUP_ERROR.search(log):
        reason = "setup_or_collection_error"
    elif public_exception is not None:
        matched, _, _ = classify_failure(public_exception, stderr, returncode)
        reason = "public_exception_candidate" if matched else "exception_contract_mismatch"
    elif _ASSERTION_ERROR.search(log):
        reason = "assertion_candidate"
    else:
        reason = "unrelated_or_unclassified_failure"
    return {
        "schema": "e1c-reproducer-dev-feedback-v1",
        "reason": reason,
        "candidate_prepatch_failure": reason in {"public_exception_candidate", "assertion_candidate"},
        "trusted_reproducer": False,
    }
