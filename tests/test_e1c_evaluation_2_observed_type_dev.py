import json

from evals import e1c_evaluation_2_observed_type_dev as runner


def test_runtime_fact_only_for_passing_exact_environment(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "_execute", lambda *a: ({"status": "target_not_repeatable_failure", "matched_public_failure_guards_still_present": [{"path": "core.py", "line": 3, "predicate": "labels", "source_sha256": "a" * 64}]}, {}, None, {}))
    root = tmp_path / "out"
    root.mkdir()
    (root / "candidate.json").write_text(json.dumps({"probe_sha256": "b" * 64}), encoding="utf-8")
    monkeypatch.setattr(runner, "observe", lambda *a: {"returncode": 0, "records": [{"observed_type": "builtins.list"}]})
    feedback, _, selected, _ = runner.execute_probe({}, {"base_commit": "base"}, tmp_path, "image", root, {})
    assert feedback["runtime_argument_types"] == [{"observed_type": "builtins.list"}] and selected is None
    assert feedback["observation_is_own_synthetic_input_not_reported_fact"]


def test_scoped_wrapper_restores_old_identity_and_budget():
    old = runner.base.OUT, runner.base.base.ready.compiled.TASK_CAP
    with runner.configured():
        assert runner.base.OUT == runner.OUT
        assert runner.base.base.ready.compiled.CAP == 50000 and runner.base.base.ready.compiled.TASK_CAP == 24000
        assert runner.base.base.ready.compiled.base.loop.execute_probe is runner.execute_probe
    assert old == (runner.base.OUT, runner.base.base.ready.compiled.TASK_CAP)
