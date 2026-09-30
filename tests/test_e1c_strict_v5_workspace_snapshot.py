import json

import evals.e1c_strict_v5_workspace_snapshot as snapshot


def test_identity_sha_ignores_git_status() -> None:
    clean = [
        {
            "path": "evals/a.py",
            "sha256": "a" * 64,
            "git_status": "  ",
            "tracked_clean": True,
        }
    ]
    dirty = [
        {
            "path": "evals/a.py",
            "sha256": "a" * 64,
            "git_status": "??",
            "tracked_clean": False,
        }
    ]
    assert snapshot._identity_sha(clean) == snapshot._identity_sha(dirty)


def test_verify_detects_changed_added_and_missing_paths(tmp_path, monkeypatch) -> None:
    root = tmp_path
    (root / "evals").mkdir()
    (root / "tests").mkdir()
    a = root / "evals" / "e1c_strict_v5_a.py"
    a.write_text("old", encoding="utf-8")
    monkeypatch.setattr(snapshot, "ROOT", root)
    monkeypatch.setattr(snapshot, "STATIC_DATA", ())
    monkeypatch.setattr(snapshot, "PROTOCOL_DOCS", ())
    monkeypatch.setattr(snapshot, "_git", lambda *args: "head" if args[0] == "rev-parse" else "")
    frozen = snapshot.build(output=root / "snap.json")
    assert frozen["identity_file_count"] == 1

    a.write_text("new", encoding="utf-8")
    b = root / "tests" / "test_e1c_strict_v5_b.py"
    b.write_text("b", encoding="utf-8")
    result = snapshot.verify(root / "snap.json")
    assert result["match"] is False
    assert result["changed_paths"] == ["evals/e1c_strict_v5_a.py"]
    assert result["added_paths"] == ["tests/test_e1c_strict_v5_b.py"]
    assert result["missing_paths"] == []


def test_build_marks_head_insufficient_when_relevant_files_are_dirty(
    tmp_path, monkeypatch
) -> None:
    root = tmp_path
    (root / "evals").mkdir()
    (root / "tests").mkdir()
    target = root / "evals" / "e1c_strict_v5_a.py"
    target.write_text("x", encoding="utf-8")
    monkeypatch.setattr(snapshot, "ROOT", root)
    monkeypatch.setattr(snapshot, "STATIC_DATA", ())
    monkeypatch.setattr(snapshot, "PROTOCOL_DOCS", ())

    def fake_git(*args):
        if args[0] == "rev-parse":
            return "deadbeef"
        return "?? evals/e1c_strict_v5_a.py"

    monkeypatch.setattr(snapshot, "_git", fake_git)
    result = snapshot.build(output=root / "snap.json")
    assert result["head"] == "deadbeef"
    assert result["head_is_sufficient_identity"] is False
    assert result["workspace_identity_required"] is True
    assert result["relevant_dirty_count"] == 1
    assert result["live_allowed"] is False


def test_mutable_diagnostics_do_not_enter_identity_sha(tmp_path, monkeypatch) -> None:
    root = tmp_path
    (root / "evals").mkdir()
    (root / "tests").mkdir()
    (root / "data").mkdir()
    code = root / "evals" / "e1c_strict_v5_a.py"
    code.write_text("x", encoding="utf-8")
    mutable = root / "data" / "e1c_strict_v5_transport_trend.json"
    mutable.write_text(json.dumps({"state": "a"}), encoding="utf-8")
    monkeypatch.setattr(snapshot, "ROOT", root)
    monkeypatch.setattr(snapshot, "STATIC_DATA", ())
    monkeypatch.setattr(snapshot, "PROTOCOL_DOCS", ())
    monkeypatch.setattr(snapshot, "_git", lambda *args: "head" if args[0] == "rev-parse" else "")
    first = snapshot.build(output=root / "snap1.json")
    mutable.write_text(json.dumps({"state": "b"}), encoding="utf-8")
    second = snapshot.build(output=root / "snap2.json")
    assert first["identity_sha256"] == second["identity_sha256"]
    assert second["mutable_diagnostic_file_count"] == 1
