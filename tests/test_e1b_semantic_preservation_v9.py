import pytest

from evals.e1b_semantic_preservation_v9 import (
    SCHEMA_VERSION,
    audit_semantic_preservation,
    require_semantic_preservation,
)


def obligations():
    return [
        {"kind": "change", "value": "failed"},
        {"kind": "identity", "value": "pending"},
    ]


def test_schema_frozen():
    assert SCHEMA_VERSION == "e1b-semantic-preservation-v1"


def test_accepts_explicit_change_and_identity_actions():
    patch = {"src/status.py": """def map_status(status):
    if status == "failed":
        return "error"
    if status == "pending":
        return status
    return status
"""}
    assert require_semantic_preservation(obligations(), patch)["semantic_preservation_complete"] is True


def test_rejects_guarded_identity_branch_that_destructively_remaps():
    patch = {"src/status.py": """def map_status(status):
    if status == "failed":
        return "error"
    if status == "pending":
        return "completed"
    return status
"""}
    report = audit_semantic_preservation(obligations(), patch)
    assert report["semantic_preservation_complete"] is False
    assert next(check for check in report["checks"] if check["value"] == "pending")["satisfied"] is False


def test_rejects_change_obligation_with_identity_action():
    patch = {"src/status.py": """def map_status(status):
    if status == "failed":
        return status
    if status == "pending":
        return status
"""}
    with pytest.raises(ValueError, match="semantic-preservation witness incomplete"):
        require_semantic_preservation(obligations(), patch)


def test_rejects_ambiguous_multi_statement_branch():
    patch = {"src/status.py": """def map_status(status):
    if status == "failed":
        log(status)
        return "error"
    if status == "pending":
        return status
"""}
    assert audit_semantic_preservation(obligations(), patch)["semantic_preservation_complete"] is False


def test_rejects_duplicate_value_guards_as_ambiguous():
    patch = {"src/status.py": """def f(status):
    if status == "failed":
        return "error"
    if status == "pending":
        return status

def g(status):
    if status == "pending":
        return status
"""}
    assert audit_semantic_preservation(obligations(), patch)["semantic_preservation_complete"] is False


def test_rejects_unsupported_non_python_participant():
    patch = {
        "src/status.py": """def f(status):
    if status == "failed":
        return "error"
    if status == "pending":
        return status
""",
        "config/status.json": "{}",
    }
    report = audit_semantic_preservation(obligations(), patch)
    assert report["unsupported_files"] == ["config/status.json"]
    assert report["semantic_preservation_complete"] is False


def test_zero_obligations_do_not_claim_semantic_success():
    report = audit_semantic_preservation([], {"src/a.py": "VALUE = 1"})
    assert report["semantic_preservation_complete"] is False
