from evals.e1b_semantic_dataflow_v9_2 import SCHEMA_VERSION, audit_semantic_dataflow, corpus_sha256


def audit(obligations, code):
    return audit_semantic_dataflow(obligations, {"x.py": code})


def test_schema():
    assert SCHEMA_VERSION == "e1b-semantic-dataflow-v1"


def test_alias_identity_is_traced_to_source():
    result = audit([{"kind": "identity", "source_value": "pending"}], """def f(status):
    current = status
    if current == "pending":
        return current
""")
    assert result["complete"] is True
    assert result["branches"][0]["variable"] == "status"


def test_alias_wrong_literal_change_rejected():
    result = audit([{"kind": "change", "source_value": "failed", "target_value": "error"}], """def f(status):
    current = status
    if current == "failed":
        return "completed"
""")
    assert result["complete"] is False


def test_bool_and_int_do_not_collide():
    result = audit([{"kind": "change", "source_value": False, "target_value": True}], """def f(flag):
    if flag == 0:
        return 1
""")
    assert result["complete"] is False


def test_match_case_literal_identity_and_change():
    code = """def f(status):
    match status:
        case "failed":
            return "error"
        case "pending":
            return status
"""
    obligations = [
        {"kind": "change", "source_value": "failed", "target_value": "error"},
        {"kind": "identity", "source_value": "pending"},
    ]
    assert audit(obligations, code)["complete"] is True


def test_static_dict_mapping_exact_target():
    code = """def f(status):
    mapping = {"failed": "error", "pending": "pending"}
    return mapping[status]
"""
    obligations = [
        {"kind": "change", "source_value": "failed", "target_value": "error"},
        {"kind": "identity", "source_value": "pending", "target_value": "pending"},
    ]
    assert audit(obligations, code)["complete"] is True


def test_static_dict_wrong_target_rejected():
    code = """def f(status):
    mapping = {"failed": "completed"}
    return mapping[status]
"""
    assert audit([{"kind": "change", "source_value": "failed", "target_value": "error"}], code)["complete"] is False


def test_call_raise_and_attribute_effects_rejected():
    call = """def f(status):
    if status == "pending":
        log(status)
        return status
"""
    raised = """def f(status):
    if status == "pending":
        raise RuntimeError()
"""
    attribute = """def f(status):
    if status == "pending":
        obj.status = status
"""
    obligation = [{"kind": "identity", "source_value": "pending"}]
    assert audit(obligation, call)["complete"] is False
    assert audit(obligation, raised)["complete"] is False
    assert audit(obligation, attribute)["complete"] is False


def test_dynamic_helper_is_not_treated_as_literal_target():
    code = """def f(status):
    if status == "failed":
        return normalize(status)
"""
    assert audit([{"kind": "change", "source_value": "failed", "target_value": "error"}], code)["complete"] is False


def test_deterministic_across_patch_and_obligation_order():
    obligations = [
        {"kind": "identity", "source_value": "pending"},
        {"kind": "change", "source_value": "failed", "target_value": "error"},
    ]
    patch = {
        "b.py": "def b(status):\n    if status == 'pending':\n        return status\n",
        "a.py": "def a(status):\n    if status == 'failed':\n        return 'error'\n",
    }
    assert audit_semantic_dataflow(obligations, patch) == audit_semantic_dataflow(list(reversed(obligations)), dict(reversed(list(patch.items()))))


def test_corpus_hash_is_stable_and_type_sensitive():
    a = [{"source": False, "target": True}]
    assert corpus_sha256(a) == corpus_sha256(list(a))
    assert corpus_sha256(a) != corpus_sha256([{"source": 0, "target": 1}])
