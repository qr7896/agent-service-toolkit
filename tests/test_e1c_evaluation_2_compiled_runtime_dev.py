import hashlib
import json

import pytest

from evals import e1c_evaluation_2_compiled_runtime_dev as runner


def context(tmp_path):
    source = "class Engine:\n    def __init__(self, count=1): pass\n    def run(self): return 20\n"
    (tmp_path / "core.py").write_bytes(source.encode())
    return {"candidate_paths": ["core.py"], "windows": [{"path": "core.py", "source_sha256": hashlib.sha256(source.encode()).hexdigest()}]}


def payload(assertion="count == 20"):
    return {"issue_quote": "support the option", "expected_quote": "should complete", "oracle": "value_relation",
            "setup_source": "from core import Engine\ne = Engine(new_option=True)",
            "control_action": "Engine().run()", "target_action": "count = e.run()", "assertion": assertion}


def test_canonical_predicate_is_locked_before_execution_and_raw_preserved(tmp_path, monkeypatch):
    observed = []

    def execute(canonical, frozen, workspace, image, root, environment, locked):
        oracle = {k: canonical[k] for k in ("issue_quote", "expected_quote", "oracle", "assertion")}
        if locked is not None and oracle != locked:
            raise ValueError("oracle_changed_after_feedback")
        observed.append(canonical)
        control = {"source": "x = 1\n"}
        runner._save(root / "control_candidate.json", control)
        for n in (1, 2):
            runner._save(root / f"control-{n}.json", {"probe_sha256": hashlib.sha256(control["source"].encode()).hexdigest(), "runs": []})
        return {"status": "control_failed"}, oracle, None, None

    monkeypatch.setattr(runner, "_execute_probe", execute)
    frozen = context(tmp_path)
    first = runner.execute_probe(payload(), frozen, tmp_path, "image", tmp_path / "first", {}, None)
    runner.execute_probe(payload("assert count == 20"), frozen, tmp_path, "image", tmp_path / "second", {}, first[1])
    assert all(p["assertion"] == "assert count == 20" for p in observed)
    record = json.loads((tmp_path / "first/compiler.json").read_bytes())
    assert record["raw_contract"]["assertion"] == "count == 20"
    assert record["canonical_contract"]["target_action"] == payload()["target_action"]
    with pytest.raises(ValueError, match="oracle_changed"):
        runner.execute_probe(payload("count == 21"), frozen, tmp_path, "image", tmp_path / "third", {}, first[1])


def test_adapter_restores_old_functions_on_failure():
    old = runner.base.loop.execute_probe, runner.base.loop.messages, runner.base.OUT
    with pytest.raises(RuntimeError), runner.configured():
        assert runner.base.loop.execute_probe is runner.execute_probe
        raise RuntimeError("test failure")
    assert old == (runner.base.loop.execute_probe, runner.base.loop.messages, runner.base.OUT)


def test_pending_initial_calls_protected_without_raising_cap():
    tasks = [{"initial_reserve": 5000}, {"initial_reserve": 7000}, {"initial_reserve": 9000}]
    assert runner.protected_ceiling(tasks, 0) == 84000
    assert runner.protected_ceiling(tasks, 1) == 91000
    assert runner.protected_ceiling(tasks, 2) == runner.CAP == 100000


@pytest.mark.parametrize("raw", ['{"shell":"pytest"}', '{"probe":{},"execution":{}}', '{"type":"unknown","retrieve":"API"}'])
def test_unknown_actions_still_fail_closed(raw):
    with pytest.raises(ValueError):
        runner.parse_action(raw)


def test_messages_make_native_coverage_and_compiler_limits_explicit():
    value = runner.messages({"issue": "ordinary software issue", "windows": []})
    assert "NOT actions" in value[0].content and "not proof of semantic equivalence" in value[0].content
    assert "Gold" not in value[1].content


def test_all_nine_inputs_are_retained_not_first_per_repository(tmp_path, monkeypatch):
    previous = tmp_path / "previous"
    tasks = []
    for n in range(9):
        iid = f"repo__task-{n}"
        path = previous / "inputs" / (iid + ".json")
        runner._save(path, {"issue": "public issue", "base_commit": "base"})
        tasks.append({"instance_id": iid, "input_sha256": runner._sha(path), "image_id": "image"})
    runner._save(previous / "freeze.json", {"fixed_denominator": 12, "tasks": tasks})
    monkeypatch.setattr(runner, "PREVIOUS", previous)
    monkeypatch.setattr(runner, "PINNED", {"freeze.json": runner._sha(previous / "freeze.json")})
    monkeypatch.setattr(runner, "verified_local_image", lambda iid: "image")
    monkeypatch.setattr(runner, "verify_workspace", lambda frozen, workspace: None)
    rows = runner.inputs()
    assert len(rows) == 9 and [t["instance_id"] for t, _, _ in rows] == [t["instance_id"] for t in tasks]
