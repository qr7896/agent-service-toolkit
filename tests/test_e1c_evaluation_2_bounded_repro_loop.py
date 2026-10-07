import hashlib
import json
import subprocess

import pytest
from langchain_core.messages import AIMessage

from evals import e1c_evaluation_2_bounded_repro_loop as loop
from evals.e1c_evaluation_2_container_health import ContainerInfrastructureUnavailable


def context(tmp_path):
    code = "class Engine:\n    def apply(self, data):\n        return data\n"
    (tmp_path / "core.py").write_bytes(code.encode())
    (tmp_path / ".gitignore").write_text("output/\nx/\n", encoding="utf-8")
    for args in (["init", "-q"], ["add", "core.py", ".gitignore"],
                 ["-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"]):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    commit = subprocess.check_output(["git", "-C", str(tmp_path), "rev-parse", "HEAD"], text=True).strip()
    return {"issue": "The production API should complete on a valid input.", "base_commit": commit,
            "input_sha256": "a" * 64, "candidate_paths": ["core.py"], "public_fixture_facts": [],
            "windows": [{"path": "core.py", "start_line": 1, "text": code,
                         "source_sha256": hashlib.sha256(code.encode()).hexdigest()}]}


def payload():
    return {"issue_quote": "production API", "expected_quote": "should complete", "oracle": "call_completes",
            "setup_source": "from core import Engine\nengine = Engine()", "control_action": "result = engine.apply([])",
            "target_action": "result = engine.apply([1])", "assertion": ""}


def execution(code=0, tail="observed", *, repeat=False):
    run = {"returncode": code, "timed_out": False, "log_tail": tail, "log_sha256": "a" * 64}
    return {"runs": [run, run] if repeat else [run], "repeatable_failure_candidate": code == 1 and repeat,
            "repeatable_nonsetup_failure": False, "network_none": True, "pull_never": True}


@pytest.mark.parametrize("action", [{"shell": "cat tests/answer.py"}, {"retrieve": "tests/answer.py"},
                                   {"read": {"path": "core.py", "start_line": True}}, {"probe": {"source": "assert True"}},
                                   {"retrieve": "Engine", "abstain_reason": "extra"}, {"abstain_reason": ""}])
def test_no_unrestricted_tools_or_relaxed_action_schema(action):
    with pytest.raises((ValueError, KeyError)):
        loop.parse_action(json.dumps(action))


def test_retrieval_filters_test_docs_and_oracle_paths_before_read(tmp_path):
    frozen = context(tmp_path)
    for folder in ("tests", "docs", ".hidden"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "secret.py").write_text("class Engine:\n    def apply(self, x):\n        return 'PRIVATE'", encoding="utf-8")
    rows, proof = loop.retrieve("Engine.apply", tmp_path)
    assert proof["matches"] == 1 and rows[0]["path"] == "core.py"
    assert "PRIVATE" not in json.dumps(rows)
    assert loop.enrich(frozen, rows)["input_sha256"] != frozen["input_sha256"]
    with pytest.raises(Exception):
        loop.window("tests/secret.py", tmp_path, 1)


def test_context_budget_and_feedback_oracle_filter(tmp_path):
    frozen = context(tmp_path)
    with pytest.raises(ValueError, match="context_budget"):
        loop.messages({**frozen, "issue": "x" * (loop.CONTEXT_CAP + 1)})
    feedback = loop.feedback_rows([execution(1, "test_patch evaluator material")])
    assert feedback == [{"status": "execution_text_filtered_by_information_boundary"}]
    assert len(loop.feedback_rows([execution(1, "x" * 9000)])[0]["observed_trace"]) == 1600


@pytest.mark.parametrize("code", [90, 125, 126, 127])
def test_infra_never_becomes_software_feedback(code):
    with pytest.raises(ContainerInfrastructureUnavailable):
        loop.checked_execution(execution(code))


def test_timeout_stops_instead_of_refining_fixture():
    value = execution(1)
    value["runs"][0]["timed_out"] = True
    with pytest.raises(ContainerInfrastructureUnavailable):
        loop.checked_execution(value)


def test_control_failure_never_executes_target(tmp_path, monkeypatch):
    frozen, calls = context(tmp_path), []
    monkeypatch.setattr(loop, "require_engine", lambda *_: True)

    def run(candidate, *_args, **_kwargs):
        calls.append(candidate["source"])
        return execution(1)

    monkeypatch.setattr(loop, "execute_candidate", run)
    feedback, lock, candidate, target = loop.execute_probe(payload(), frozen, tmp_path, "image", tmp_path / "output", {"missing_optional_import": None})
    assert feedback["status"] == "control_failed" and len(calls) == 2
    assert all("engine.apply([])" in source and "engine.apply([1])" not in source for source in calls)
    assert candidate is target is None and lock["oracle"] == "call_completes"


def test_oracle_change_and_native_harness_rejected_before_execution(tmp_path, monkeypatch):
    frozen = context(tmp_path)
    monkeypatch.setattr(loop, "execute_candidate", lambda *_a, **_k: pytest.fail("must not execute"))
    lock = {k: payload()[k] for k in ("issue_quote", "expected_quote", "oracle", "assertion")}
    with pytest.raises(ValueError, match="oracle_changed"):
        loop.execute_probe({**payload(), "expected_quote": "valid input"}, frozen, tmp_path, "image", tmp_path / "x", {}, lock)
    with pytest.raises(ValueError, match="native_test_harness"):
        loop.execute_probe({**payload(), "setup_source": "import pytest\npytest.main([])"}, frozen, tmp_path, "image", tmp_path / "x", {})
    with pytest.raises(ValueError, match="tautological"):
        loop.execute_probe({**payload(), "oracle": "value_relation", "assertion": "assert result == result"}, frozen, tmp_path, "image", tmp_path / "x", {})


@pytest.mark.asyncio
async def test_full_retrieve_execute_observe_refine_and_selection_before_grader(tmp_path, monkeypatch):
    frozen = context(tmp_path)
    monkeypatch.setattr(loop, "require_engine", lambda *_: True)
    actions = [{"retrieve": "Engine.apply"}, {"probe": payload()}, {"probe": {**payload(), "target_action": "result = engine.apply([2])"}}]
    feedback_seen, calls = [], []

    async def invoke(messages, turn):
        feedback_seen.append(json.loads(messages[-1].content)["last_feedback"])
        return AIMessage(content=json.dumps(actions[turn - 1]))

    def run(candidate, _image, _base, artifact, **_kwargs):
        artifact.mkdir(parents=True)
        (artifact / (candidate["probe_sha256"] + ".py")).write_bytes(candidate["source"].encode())
        calls.append(candidate)
        return execution(1, repeat=True) if "engine.apply([2])" in candidate["source"] else execution()

    monkeypatch.setattr(loop, "execute_candidate", run)
    result = await loop.run_task(frozen, tmp_path, "image", tmp_path / "output", {"missing_optional_import": None}, invoke)
    assert result["status"] == "executed" and result["selected_turn"] == 3 and not result["trusted_reproducer"]
    assert feedback_seen[2]["status"] == "target_not_repeatable_failure" and len(calls) == 6
    assert (tmp_path / "output/candidate.json").exists()
    assert not (tmp_path / "output/gold-discrimination").exists()


@pytest.mark.asyncio
async def test_provider_error_is_not_retried(tmp_path):
    calls = []

    async def invoke(*_):
        calls.append(1)
        raise TimeoutError("provider unavailable")

    with pytest.raises(TimeoutError):
        await loop.run_task(context(tmp_path), tmp_path, "image", tmp_path / "output", {}, invoke)
    assert calls == [1]


@pytest.mark.asyncio
async def test_read_cannot_open_unexposed_file(tmp_path):
    frozen = context(tmp_path)
    seen = []

    async def invoke(messages, turn):
        seen.append(json.loads(messages[-1].content)["last_feedback"])
        action = {"read": {"path": "unknown.py", "start_line": 1}} if turn == 1 else {"abstain_reason": "missing exposed path"}
        return AIMessage(content=json.dumps(action))

    result = await loop.run_task(frozen, tmp_path, "image", tmp_path / "output", {}, invoke)
    assert result["status"] == "abstained" and seen[1]["reason"] == "read_path_was_not_exposed"


def test_smoke_one_shot_and_missing_positive_gate(tmp_path, monkeypatch):
    from evals import e1c_evaluation_2_bounded_repro_dev as runner

    monkeypatch.setattr(runner, "SMOKE", tmp_path)
    (tmp_path / "result.json").write_text(json.dumps({"cross_repository_positive_control_gate": False, "provider_calls": 0}), encoding="utf-8")
    with pytest.raises(ValueError, match="real isolated"):
        runner.freeze()


@pytest.mark.asyncio
async def test_loop_turn_limit_stops_without_extra_model_call(tmp_path):
    frozen, calls = context(tmp_path), []

    async def invoke(*_):
        calls.append(1)
        return AIMessage(content='{"shell":"unsupported"}')

    result = await loop.run_task(frozen, tmp_path, "image", tmp_path / "output", {}, invoke)
    assert result["status"] == "turn_limit" and len(calls) == 4


def test_changed_generation_seal_rejected_before_grader_import(tmp_path, monkeypatch):
    from evals import e1c_evaluation_2_bounded_repro_dev as runner

    monkeypatch.setattr(runner, "OUT", tmp_path)
    (tmp_path / "candidate.json").write_text("changed", encoding="utf-8")
    (tmp_path / "generation-seal.json").write_text(json.dumps({"files": {"candidate.json": "a" * 64}}), encoding="utf-8")
    with pytest.raises(ValueError, match="artifacts changed"):
        runner.grade()
    assert not (tmp_path / "gold-discrimination").exists()
