from evals.e1b_semantic_effect_v9_1 import (
    SCHEMA_VERSION,
    audit_semantic_effect,
    require_semantic_effect,
)


def test_schema_is_separate_from_v9():
    assert SCHEMA_VERSION == "e1b-semantic-effect-v1"


def test_exact_string_target_accepts_only_requested_target():
    obligations = [{"kind": "change", "source_value": "failed", "target_value": "error"}]
    good = {"x.py": "def f(status):\n    if status == 'failed':\n        return 'error'\n"}
    bad = {"x.py": "def f(status):\n    if status == 'failed':\n        return 'completed'\n"}
    assert require_semantic_effect(obligations, good)["semantic_effect_complete"] is True
    assert audit_semantic_effect(obligations, bad)["semantic_effect_complete"] is False


def test_bool_and_integer_targets_are_exact():
    bool_obligation = [{"kind": "change", "source_value": False, "target_value": True}]
    int_obligation = [{"kind": "change", "source_value": 1, "target_value": 2}]
    assert require_semantic_effect(bool_obligation, {"x.py": "def f(flag):\n    if flag is False:\n        return True\n"})
    assert require_semantic_effect(int_obligation, {"x.py": "def f(version):\n    if version == 1:\n        return 2\n"})


def test_identity_requires_identity_action():
    obligations = [{"kind": "identity", "source_value": "pending"}]
    good = {"x.py": "def f(status):\n    if status == 'pending':\n        return status\n"}
    bad = {"x.py": "def f(status):\n    if status == 'pending':\n        return 'pending'\n"}
    assert require_semantic_effect(obligations, good)
    assert audit_semantic_effect(obligations, bad)["semantic_effect_complete"] is False


def test_legacy_change_without_target_is_labeled_unavailable():
    obligations = [{"kind": "change", "source_value": "failed"}]
    report = require_semantic_effect(obligations, {"x.py": "def f(status):\n    if status == 'failed':\n        return 'anything'\n"})
    assert report["checks"][0]["target_verification"] == "unavailable"


def test_obvious_call_side_effect_fails_closed():
    obligations = [{"kind": "identity", "source_value": "pending"}]
    patch = {"x.py": "def f(status):\n    if status == 'pending':\n        log(status)\n        return status\n"}
    assert audit_semantic_effect(obligations, patch)["semantic_effect_complete"] is False


def test_attribute_and_subscript_writes_fail_closed():
    obligations = [{"kind": "change", "source_value": 1, "target_value": 2}]
    attribute = {"x.py": "def f(version, obj):\n    if version == 1:\n        obj.version = 2\n"}
    subscript = {"x.py": "def f(version, data):\n    if version == 1:\n        data['version'] = 2\n"}
    assert audit_semantic_effect(obligations, attribute)["semantic_effect_complete"] is False
    assert audit_semantic_effect(obligations, subscript)["semantic_effect_complete"] is False


def test_duplicate_guards_fail_closed():
    obligations = [{"kind": "identity", "source_value": "pending"}]
    patch = {"x.py": "def f(x):\n    if x == 'pending':\n        return x\ndef g(y):\n    if y == 'pending':\n        return y\n"}
    assert audit_semantic_effect(obligations, patch)["semantic_effect_complete"] is False


def test_non_python_and_zero_obligations_do_not_pass():
    assert audit_semantic_effect([], {"x.py": "VALUE = 1"})["semantic_effect_complete"] is False
    report = audit_semantic_effect([{"kind": "change", "source_value": 1}], {"x.json": "{}"})
    assert report["unsupported_files"] == ["x.json"]
    assert report["semantic_effect_complete"] is False


def test_output_order_is_deterministic():
    obligations = [
        {"kind": "identity", "source_value": "pending"},
        {"kind": "change", "source_value": "failed", "target_value": "error"},
    ]
    a = {"b.py": "def g(x):\n    if x == 'pending':\n        return x\n", "a.py": "def f(x):\n    if x == 'failed':\n        return 'error'\n"}
    b = dict(reversed(list(a.items())))
    assert audit_semantic_effect(obligations, a) == audit_semantic_effect(list(reversed(obligations)), b)
