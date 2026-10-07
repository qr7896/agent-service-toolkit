import json

from evals import e1c_evaluation_2_unified_policy_dev as runner


def test_one_system_replaces_legacy_append_and_preserves_evidence():
    frozen = {"issue": "Public API should complete.", "windows": [], "public_fixture_facts": []}
    with runner.configured():
        value = runner.messages(frozen, {"status": "own_observation"}, None)
    assert value[0].content == runner.POLICY
    assert "Unknown semantics require abstention" not in value[0].content
    assert "Lack of a reported type alone does NOT forbid" in value[0].content
    assert "Missing desired behavior requires abstention" in value[0].content
    assert "Never access original tests" in value[0].content and "No tautologies" in value[0].content
    body = json.loads(value[1].content)
    assert "".join(text for _, text in body["public_issue_spans"]) == frozen["issue"]
    assert body["last_feedback"] == {"status": "own_observation"}


def test_hypothesis_ledger_does_not_promote_report_facts(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "_execute", lambda *a: ("delegated", None, None, None))
    payload = {"setup_source": "labels = ['a']", "target_action": "api(labels=labels)"}
    assert runner.execute_probe(payload, {}, tmp_path, "image", tmp_path / "out", {})[0] == "delegated"
    ledger = json.loads((tmp_path / "out/uncertainty-ledger.json").read_bytes())
    assert not ledger["report_exactness_proven"] and not ledger["controller_modified_probe"]
    assert ledger["arguments"]["rows"][0]["provenance"] == "model_fixture_hypothesis_or_unknown"


def test_scope_restores_old_policy_and_keeps_budget():
    old = runner.base.OUT, runner._compiled.conversation, runner._compiled.base.loop.execute_probe
    with runner.configured():
        assert runner._compiled.CAP == 50000 and runner._compiled.TASK_CAP == 24000
        assert runner._compiled.conversation is runner.conversation
    assert old == (runner.base.OUT, runner._compiled.conversation, runner._compiled.base.loop.execute_probe)
