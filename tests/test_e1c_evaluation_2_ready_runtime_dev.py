import hashlib
import json

import pytest
from langchain_core.messages import AIMessage

from evals import e1c_evaluation_2_ready_runtime_dev as runner
from evals.e1c_evaluation_2_issue_quote_refs import catalogue

ISSUE = "Reported production call fails.\nIt should return the documented result.\n"


def payload():
    return {"issue_quote_ref": 0, "expected_quote_ref": 1, "oracle": "value_relation",
            "setup_source": "from core import Engine", "control_action": "Engine().run()",
            "target_action": "result = Engine().run()", "assertion": "result['x'] == 1"}


def test_actual_envelope_and_reference_dto_resolve_without_quote_invention():
    action, value, proof = runner.decode(json.dumps({"type": "json_object", "content": {"probe": payload()}}), ISSUE)
    assert action == "probe" and value["expected_quote"] == catalogue(ISSUE)["spans"][1]["text"]
    assert proof["envelope"]["known_envelope_removed"] and value["assertion"] == payload()["assertion"]


@pytest.mark.parametrize("value", [{"type": "json_object", "content": {"probe": payload()}, "shell": "pytest"},
    {"type": "json_object", "content": {"shell": "pytest"}}, {"type": "json_object", "content": json.dumps({"probe": payload()})},
    {"probe": {**payload(), "expected_quote_ref": True}}, {"probe": {**payload(), "expected_quote_ref": 9}}])
def test_extra_unrestricted_and_invalid_refs_rejected(value):
    with pytest.raises(ValueError):
        runner.decode(json.dumps(value), ISSUE)


def test_compact_spans_lossless_and_actual_observation_not_duplicated():
    frozen = {"issue": ISSUE, "windows": [], "public_fixture_facts": []}
    with runner.configured():
        _, canonical, _ = runner.decode(json.dumps({"probe": payload()}), ISSUE)
        observed = {"status": "unique_observation_marker"}
        prior = json.dumps({"probe": payload()})
        msgs = runner.messages(frozen, observed, canonical)
        assert "".join(text for _, text in json.loads(msgs[1].content)["public_issue_spans"]) == ISSUE
        result = runner.conversation(msgs, 2, prior, observed)
        assert sum(str(m.content).count("unique_observation_marker") for m in result) == 1
        assert "previous_probe" not in result[1].content and result[2].content == prior
        assert "two integer quote references" in result[-1].content
        assert "seven strings" not in result[0].content


def test_readiness_sends_unevaluated_predicate_back_without_selecting(tmp_path, monkeypatch):
    source = "result = api()\nassert result['x'] == 1\n"
    sha = hashlib.sha256(source.encode()).hexdigest()
    candidate = {"source": source, "probe_sha256": sha}
    execution = {"probe_sha256": sha, "runs": [{"returncode": 1, "log_tail": 'Traceback:\n  File "/e1c2_probe.py", line 2, in <module>\nTypeError: invalid index'}]}

    def run(*args):
        runner._save(args[4] / "candidate.json", candidate)
        return {"status": "base_witness_semantics_unverified"}, {"oracle": "value_relation"}, candidate, execution

    monkeypatch.setattr(runner, "_execute", run)
    feedback, lock, selected, result = runner.execute_probe({}, {}, tmp_path, "image", tmp_path / "out", {})
    assert feedback["status"] == "oracle_evaluation_error_requires_feedback" and selected is None
    assert result is execution and lock == {"oracle": "value_relation"}


@pytest.mark.asyncio
async def test_two_same_invalid_actions_stop_before_third_call(tmp_path):
    calls = []

    async def invoke(msgs, turn):
        calls.append(turn)
        return AIMessage(content='{"shell":"unsupported"}')

    with runner.configured():
        result = await runner.run_task({"issue": ISSUE, "windows": []}, tmp_path, "image", tmp_path / "out", {}, invoke)
    assert calls == [1, 2] and result["status"] == "repeated_unsuccessful_action_stop"


def test_process_local_adapter_restores_all_old_functions():
    original = runner.compiled.CAP, runner.compiled.inputs, runner.compiled.base.loop.run_task
    with runner.configured():
        assert runner.compiled.CAP == 50000 and runner.compiled.base.loop.run_task is runner.run_task
    assert original == (runner.compiled.CAP, runner.compiled.inputs, runner.compiled.base.loop.run_task)


@pytest.mark.asyncio
async def test_readiness_feedback_allows_fixture_revision_but_locks_expectation(tmp_path, monkeypatch):
    actions = [payload(), {**payload(), "target_action": "result = Engine().run().data"}]
    seen, locks = [], []

    async def invoke(msgs, turn):
        seen.append(json.loads(msgs[1].content)["last_feedback"])
        return AIMessage(content=json.dumps({"probe": actions[turn - 1]}))

    def execute(value, frozen, workspace, image, root, environment, locked):
        oracle = {k: value[k] for k in ("issue_quote", "expected_quote", "oracle", "assertion")}
        if locked is not None:
            assert oracle == locked
        locks.append(oracle)
        source = value["target_action"] + "\nassert result['x'] == 1\n"
        sha = hashlib.sha256(source.encode()).hexdigest()
        kind = "AssertionError" if ".data" in source else "TypeError"
        log = f'Traceback:\n  File "/e1c2_probe.py", line 2, in <module>\n{kind}: comparison'
        candidate = {"source": source, "probe_sha256": sha}
        execution = {"probe_sha256": sha, "runs": [{"returncode": 1, "log_tail": log} for _ in (1, 2)]}
        runner._save(root / "candidate.json", candidate)
        (root / "execution").mkdir()
        return {"status": "base_witness_semantics_unverified"}, oracle, candidate, execution

    monkeypatch.setattr(runner, "_execute", execute)
    with runner.configured():
        result = await runner.run_task({"issue": ISSUE, "windows": []}, tmp_path, "image", tmp_path / "out", {}, invoke)
    assert result["status"] == "executed" and result["selected_turn"] == 2
    assert seen[1]["status"] == "oracle_evaluation_error_requires_feedback"
    assert locks[0] == locks[1] and not result["trusted_reproducer"]
