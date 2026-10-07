import json

import pytest

from evals import e1c_evaluation_2_obligation_dev as runner


def test_unfulfilled_goal_stops_before_execution_and_does_not_lock_oracle(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "verify_entrypoint", lambda *a: {"status": "unfulfilled_or_unknown", "rows": [{"status": "missing"}]})
    monkeypatch.setattr(runner, "_execute", lambda *a: pytest.fail("must not execute"))
    feedback, lock, candidate, execution = runner.execute_probe({"setup_source": "from core import Engine", "target_action": "Engine()"}, {}, tmp_path, "image", tmp_path / "out", {})
    assert feedback["reason"] == "explicit_api_obligation_unfulfilled_or_unproven" and feedback["oracle_not_locked"]
    assert lock is candidate is execution is None


def test_obligation_feedback_does_not_add_probe_fields_or_change_old_budget():
    original = runner.base.OUT, runner.base.ready.compiled.TASK_CAP, runner.base.ready.compiled.CAP
    with runner.configured():
        messages = runner.messages({"issue": "Please expose `option` in `Engine.__init__()`.", "windows": []})
        body = json.loads(messages[1].content)
        assert body["explicit_api_obligations"][0]["parameter"] == "option"
        assert "schema/source/explicit-API-obligation-valid" in messages[0].content
        assert "SAME seven probe fields" in messages[0].content
        assert runner.base.ready.compiled.TASK_CAP == 24000 and runner.base.ready.compiled.CAP == 50000
    assert original == (runner.base.OUT, runner.base.ready.compiled.TASK_CAP, runner.base.ready.compiled.CAP)


def test_passing_fixture_receives_source_condition_and_hypothesis_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "verify_entrypoint", lambda *a: {"status": "not_applicable", "rows": []})
    monkeypatch.setattr(runner, "_execute", lambda *a: ({"status": "target_not_repeatable_failure"}, {"oracle": "call_completes"}, None, {"own": "execution"}))
    monkeypatch.setattr(runner, "guard_evidence", lambda *a: {"rows": [{"path": "core.py", "line": 3, "predicate": "labels", "source_sha256": "source", "already_visible": True, "matches_public_failure_condition": True}]})
    payload = {"setup_source": "labels = ['a', 'b']", "target_action": "api(labels=labels)"}
    feedback, lock, candidate, execution = runner.execute_probe(payload, {}, tmp_path, "image", tmp_path / "out", {})
    assert feedback["matched_public_failure_guards_still_present"][0]["already_visible"]
    assert feedback["argument_provenance"][0]["provenance"] == "model_fixture_hypothesis_or_unknown"
    assert lock == {"oracle": "call_completes"} and candidate is None and execution == {"own": "execution"}
