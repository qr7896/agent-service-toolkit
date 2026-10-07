import hashlib

from evals.e1c_evaluation_2_public_normal_diagnostic import derive

ISSUE = "It works for\npkg.normal(model, output=None, count=4, labels=names)\nbut not for\npkg.broken(model, count=4, labels=names)\n"
PAYLOAD = {"setup_source": "from pkg import broken", "target_action": "broken(model, count=4, labels=names)",
           "control_action": "broken(model, count=4)", "oracle": "call_completes", "assertion": "",
           "issue_quote": "but not for", "expected_quote": "It works for"}


def context(tmp_path):
    source = b"def normal(model, output, count, labels):\n    return labels\ndef broken(model, count, labels):\n    return labels\n"
    (tmp_path / "pkg.py").write_bytes(source)
    return {"issue": ISSUE, "windows": [{"path": "pkg.py", "source_sha256": hashlib.sha256(source).hexdigest()}]}


def test_diagnostic_derives_public_normal_preserves_owned_input_and_marks_origin(tmp_path):
    original = dict(PAYLOAD)
    derived, proof = derive(PAYLOAD, context(tmp_path), tmp_path)
    assert PAYLOAD == original and derived["target_action"] == PAYLOAD["target_action"]
    assert "labels=names" in derived["control_action"] and "output=None" in derived["control_action"]
    assert proof["derived_program_is_not_Agent_score"] and not proof["model_generated"]
    assert not proof["semantic_alignment_proven"] and not proof["live_integrated"]


def test_unknown_extra_public_argument_not_invented(tmp_path):
    frozen = context(tmp_path)
    frozen["issue"] = ISSUE.replace("output=None", "output=unknown")
    assert derive(PAYLOAD, frozen, tmp_path) is None


def test_shadowed_normal_function_rejected(tmp_path):
    assert derive({**PAYLOAD, "setup_source": "from pkg import broken\nnormal = broken"}, context(tmp_path), tmp_path) is None
