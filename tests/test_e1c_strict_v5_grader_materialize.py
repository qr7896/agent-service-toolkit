import json

import evals.e1c_strict_v5_grader_materialize as materialize
from evals.e1c_strict_v5_grader_materialize import FILES


def test_grader_files_are_explicit_and_isolated() -> None:
    assert set(FILES) == {
        "tests.json",
        "gold.patch",
        "test.patch",
        "eval.sh",
        "Dockerfile",
    }


def test_run_reuses_existing_grader_files_without_refetch(tmp_path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "source_revision": "rev-1",
        "tasks": [{
            "instance_id": "task-1",
            "repo": "org/repo",
            "base_commit": "a" * 40,
            "image": "image:latest",
        }],
    }), encoding="utf-8")
    out_root = tmp_path / "grader"
    task_root = out_root / "task-1"
    task_root.mkdir(parents=True)
    for name in FILES:
        (task_root / name).write_bytes(name.encode())
    calls = []
    monkeypatch.setattr(materialize, "MANIFEST", manifest)
    monkeypatch.setattr(materialize, "OUT_ROOT", out_root)
    monkeypatch.setattr(materialize, "certify", lambda output=None: {"ready": True})
    monkeypatch.setattr(materialize, "_fetch", lambda *args: calls.append(args))
    result = materialize.run(tmp_path / "summary.json")
    assert result["ready"] is True
    assert calls == []
    assert all(
        item["status"] == "already_materialized"
        for row in result["rows"]
        for item in row["files"]
    )
