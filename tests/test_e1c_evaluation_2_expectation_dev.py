import hashlib

import pytest

from evals import e1c_evaluation_2_expectation_dev as runner

ISSUE = "The public API should complete.\nIt works for\npkg.normal(model, count=4, labels=names)\nbut not for\npkg.broken(model, count=4, labels=names)\n"
PAYLOAD = {"setup_source": "from pkg import normal, broken", "control_action": "normal(model, count=4, labels=names)",
           "target_action": "broken(model, count=4, labels=names)", "assertion": "", "oracle": "call_completes",
           "expected_quote": "The public API should complete.", "issue_quote": "but not for"}


def frozen(tmp_path):
    source = b"def normal(model, count, labels):\n    return labels\ndef broken(model, count, labels):\n    return labels\n"
    (tmp_path / "pkg.py").write_bytes(source)
    return {"issue": ISSUE, "windows": [{"path": "pkg.py", "source_sha256": hashlib.sha256(source).hexdigest()}]}


def test_public_contrast_bound_without_value_or_semantic_certificate(tmp_path):
    value = runner.contrast_binding(PAYLOAD, frozen(tmp_path), tmp_path)
    assert value["status"] == "explicit_contrast_exercised_syntactically" and len(value["source_bindings"]) == 2
    assert not value["semantic_alignment_proven"] and not value["actual_shared_values_proven"]


@pytest.mark.parametrize("change", [
    {"control_action": "broken(model, count=4)"},
    {"control_action": "normal(model, count=4)"},
    {"target_action": "broken(model, count=3, labels=names)"},
    {"target_action": "broken(model, count=4, labels=other_names)"},
    {"setup_source": "from pkg import normal, broken\nnormal = broken"},
])
def test_omission_wrong_api_literals_inputs_or_shadowing_not_fulfilled(tmp_path, change):
    assert runner.contrast_binding({**PAYLOAD, **change}, frozen(tmp_path), tmp_path)["status"] == "unfulfilled_or_unknown"


def test_changed_exposed_source_rejected(tmp_path):
    context = frozen(tmp_path)
    (tmp_path / "pkg.py").write_bytes(b"def normal(*args):\n    return None\n")
    with pytest.raises(ValueError, match="contrast source"):
        runner.contrast_binding(PAYLOAD, context, tmp_path)


def test_ambiguous_public_call_blocks_not_guessed():
    assert runner.public_contrast(ISSUE + "pkg.another(model)\n") is None


@pytest.mark.parametrize("quote", ['File "/tmp/core.py", line 4, in api', "Traceback:\nValid API should complete.", "if values:"])
def test_trace_mixed_trace_and_incomplete_guard_not_expectations(quote):
    assert runner.gate_role(quote) in runner.BAD_ROLES


def test_bad_quote_rejected_before_delegate_or_lock(tmp_path, monkeypatch):
    quote = 'File "/testbed/core.py", line 4, in api'
    payload = {**PAYLOAD, "expected_quote": quote}
    monkeypatch.setattr(runner, "_execute", lambda *a: pytest.fail("delegate must not run"))
    result = runner.execute_probe(payload, {"issue": ISSUE + quote}, tmp_path, "image", tmp_path, {}, None)
    assert result[0]["status"] == "action_rejected" and result[0]["oracle_not_locked"]
    assert result[1:] == (None, None, None)


def test_unknown_prose_not_automatically_trusted():
    assert runner.gate_role("Can somebody help with this problem?") not in runner.BAD_ROLES
    assert runner.gate_role("Can somebody help with this problem?") == "unclassified_requires_semantic_evidence"


def test_inner_runner_configuration_preserves_new_gate_and_restores():
    old = runner._compiled.execute_probe, runner._compiled.base.loop.execute_probe
    with runner.configured():
        with runner._compiled.configured():
            assert runner._compiled.base.loop.execute_probe is runner.execute_probe
            assert runner._compiled.CAP == 50000 and runner._compiled.TASK_CAP == 24000
    assert (runner._compiled.execute_probe, runner._compiled.base.loop.execute_probe) == old
