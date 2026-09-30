from evals.e1b_semantic_helper_v9_3 import (
    MAX_HELPER_DEPTH,
    SCHEMA_VERSION,
    audit_helper_semantics,
    corpus_sha256,
)


def run(obligations, code):
    return audit_helper_semantics(obligations, {"x.py": code})


def test_schema_and_depth():
    assert SCHEMA_VERSION == "e1b-semantic-helper-v1"
    assert MAX_HELPER_DEPTH == 1


def test_exact_target_through_one_helper():
    code = """def normalize(status):
    if status == "failed":
        return "error"

def caller(status):
    return normalize(status)
"""
    assert run([{"kind": "change", "source_value": "failed", "target_value": "error"}], code)["complete"] is True


def test_identity_through_helper():
    code = """def preserve(status):
    if status == "pending":
        return status

def caller(status):
    return preserve(status)
"""
    assert run([{"kind": "identity", "source_value": "pending"}], code)["complete"] is True


def test_wrong_target_rejected():
    code = """def normalize(status):
    if status == "failed":
        return "completed"

def caller(status):
    return normalize(status)
"""
    assert run([{"kind": "change", "source_value": "failed", "target_value": "error"}], code)["complete"] is False


def test_side_effect_helper_rejected():
    code = """def normalize(status):
    log(status)
    if status == "failed":
        return "error"

def caller(status):
    return normalize(status)
"""
    result = run([{"kind": "change", "source_value": "failed", "target_value": "error"}], code)
    assert result["complete"] is False
    assert result["rejected_helpers"]["x.py::normalize"] == "nested_call"


def test_nested_helper_exceeds_depth_bound():
    code = """def inner(status):
    if status == "failed":
        return "error"

def outer(status):
    return inner(status)

def caller(status):
    return outer(status)
"""
    result = run([{"kind": "change", "source_value": "failed", "target_value": "error"}], code)
    assert result["complete"] is False
    assert result["rejected_helpers"]["x.py::outer"] == "nested_call"


def test_recursion_rejected():
    code = """def normalize(status):
    return normalize(status)

def caller(status):
    return normalize(status)
"""
    assert run([{"kind": "change", "source_value": "failed"}], code)["complete"] is False


def test_bool_int_are_typed():
    code = """def normalize(flag):
    if flag == 0:
        return 1

def caller(flag):
    return normalize(flag)
"""
    assert run([{"kind": "change", "source_value": False, "target_value": True}], code)["complete"] is False


def test_match_helper_supported():
    code = """def normalize(status):
    match status:
        case "failed":
            return "error"
        case "pending":
            return status

def caller(status):
    return normalize(status)
"""
    obligations = [
        {"kind": "change", "source_value": "failed", "target_value": "error"},
        {"kind": "identity", "source_value": "pending"},
    ]
    assert run(obligations, code)["complete"] is True


def test_attribute_access_helper_rejected():
    code = """def normalize(status):
    if status == "failed":
        return status.value

def caller(status):
    return normalize(status)
"""
    assert run([{"kind": "change", "source_value": "failed"}], code)["complete"] is False


def test_deterministic_and_corpus_hash_type_sensitive():
    obligations = [{"kind": "identity", "source_value": "pending"}]
    patch = {"x.py": "def h(x):\n    if x == 'pending':\n        return x\ndef c(x):\n    return h(x)\n"}
    assert audit_helper_semantics(obligations, patch) == audit_helper_semantics(list(reversed(obligations)), dict(reversed(list(patch.items()))))
    assert corpus_sha256([{"x": False}]) != corpus_sha256([{"x": 0}])
