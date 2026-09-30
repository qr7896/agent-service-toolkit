import hashlib
from types import SimpleNamespace

from evals.e1c_strict_v7_postfreeze import fetch_statement_bounded, run


def test_bounded_statement_fetch_reuses_existing_exact_path(tmp_path) -> None:
    path = tmp_path / "problem_statement.md"
    path.write_text("already frozen statement", encoding="utf-8")
    text, digest = fetch_statement_bounded("task", "rev", path)
    assert text == "already frozen statement"
    assert digest == hashlib.sha256(b"already frozen statement").hexdigest()


def test_bounded_statement_fetch_uses_curl_before_urllib(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("evals.e1c_strict_v7_postfreeze.shutil.which", lambda name: "curl")
    monkeypatch.setattr(
        "evals.e1c_strict_v7_postfreeze.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=b"from curl", stderr=b""),
    )
    monkeypatch.setattr(
        "evals.e1c_strict_v7_postfreeze.fetch_statement",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("urllib fallback not expected")),
    )
    text, digest = fetch_statement_bounded("task", "rev", tmp_path / "missing.md")
    assert text == "from curl"
    assert digest == hashlib.sha256(b"from curl").hexdigest()


def test_v7_postfreeze_gates_on_executable_not_merely_typed_candidates(tmp_path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"source_revision":"rev","tasks":['
        '{"instance_id":"a","repo":"o/r","base_commit":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","image":"i:a"},'
        '{"instance_id":"b","repo":"o/r","base_commit":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","image":"i:b"},'
        '{"instance_id":"c","repo":"o/r","base_commit":"cccccccccccccccccccccccccccccccccccccccc","image":"i:c"}]}'
    )
    monkeypatch.setattr("evals.e1c_strict_v7_postfreeze.ROOT", tmp_path)
    monkeypatch.setattr("evals.e1c_strict_v7_postfreeze.MANIFEST", manifest)
    monkeypatch.setattr("evals.e1c_strict_v7_postfreeze.ROOT_OUT", tmp_path / "out")
    monkeypatch.setattr("evals.e1c_strict_v7_postfreeze.certify_identity", lambda: {"ready": True, "instance_ids": ["a", "b", "c"]})
    monkeypatch.setattr("evals.e1c_strict_v7_postfreeze.fetch_statement_bounded", lambda instance_id, revision, cache_path: ("issue", "a" * 64))
    monkeypatch.setattr("evals.e1c_strict_v7_postfreeze.materialize_source", lambda task, destination: {"ready": True, "status": "ok"})
    monkeypatch.setattr("evals.e1c_strict_v7_postfreeze.build_bundle", lambda **kwargs: {"issue": "issue", "localization": {"candidates": []}})
    plans = iter([
        {"candidate_count": 1, "executable_candidate_count": 0},
        {"candidate_count": 1, "executable_candidate_count": 1},
        {"candidate_count": 1, "executable_candidate_count": 0},
    ])
    monkeypatch.setattr("evals.e1c_strict_v7_postfreeze.freeze_typed_plan", lambda issue, localization: next(plans))
    result = run(output=tmp_path / "assessment.json")
    assert result["typed_candidate_task_count"] == 3
    assert result["executable_candidate_task_count"] == 1
    assert result["candidate_gate_passed"] is False
    assert result["image_pull_allowed_by_candidate_gate"] is False
