import json

from evals import e1c_cohort_prepare as prep


def test_classify_admitted(monkeypatch, tmp_path):
    monkeypatch.setattr(prep, "OUT", tmp_path)
    task = tmp_path / "tasks" / "x"
    task.mkdir(parents=True)
    task.joinpath("task.yaml").write_text("image: swebench/example:latest\n", encoding="utf-8")
    out = tmp_path / "admission_v2" / "x"
    out.mkdir(parents=True)
    for phase in ("base", "gold"):
        out.joinpath(f"{phase}.json").write_text(
            json.dumps({"phase_pass": True, "source_identity_valid": True}), encoding="utf-8"
        )
    monkeypatch.setattr(prep.subprocess, "run", lambda *a, **k: type("R", (), {"returncode": 0})())
    row = prep.classify("x")
    assert row["admitted"] is True
    assert row["classification"] == "admitted"


def test_classify_source_invalid_is_not_admitted(monkeypatch, tmp_path):
    monkeypatch.setattr(prep, "OUT", tmp_path)
    task = tmp_path / "tasks" / "x"
    task.mkdir(parents=True)
    task.joinpath("task.yaml").write_text("image: swebench/example:latest\n", encoding="utf-8")
    out = tmp_path / "admission_v2" / "x"
    out.mkdir(parents=True)
    out.joinpath("base.json").write_text(
        json.dumps({"phase_pass": False, "source_identity_valid": False}), encoding="utf-8"
    )
    monkeypatch.setattr(prep.subprocess, "run", lambda *a, **k: type("R", (), {"returncode": 1})())
    row = prep.classify("x")
    assert row["admitted"] is False
    assert row["classification"] == "task_invalid_source_identity"


def test_replacement_can_complete_only_full_deterministic_prefix(monkeypatch, tmp_path):
    monkeypatch.setattr(prep, "OUT", tmp_path)
    monkeypatch.setattr(prep, "TARGET", 2)
    original = [{"instance_id": "a", "repo": "r/a", "base_commit": "1"}, {"instance_id": "b", "repo": "r/b", "base_commit": "2"}]
    replacement = {"instance_id": "c", "repo": "r/c", "base_commit": "3"}
    (tmp_path / "candidate_manifest.json").write_text(json.dumps({"tasks": original}), encoding="utf-8")
    monkeypatch.setattr(prep, "select", lambda *_args, **_kwargs: [*original, replacement])
    monkeypatch.setattr(prep, "classify", lambda iid: {"instance_id": iid, "admitted": iid != "b", "base_recorded": True, "gold_recorded": True, "image_local": True})
    complete = prep.build_status(3, cache_only=False)
    assert complete["admitted_count"] == 2
    assert complete["ready_to_freeze_final_cohort"] is True
    prep.write_status(complete)
    final = json.loads((tmp_path / "final_admitted_manifest.json").read_text(encoding="utf-8"))
    assert [row["instance_id"] for row in final["tasks"]] == ["a", "c"]
    assert final["tasks"][1]["base_commit"] == "3"
    partial = prep.build_status(3, cache_only=True)
    assert partial["ready_to_freeze_final_cohort"] is False
