from pathlib import Path

from evals.e1c_strict_v5_postfreeze import materialize_source


def test_materialize_source_reuses_exact_existing_head(tmp_path: Path, monkeypatch) -> None:
    dest = tmp_path / "source"
    (dest / ".git").mkdir(parents=True)
    monkeypatch.setattr(
        "evals.e1c_strict_v5_postfreeze._git_head",
        lambda path: "a" * 40,
    )
    result = materialize_source(
        {
            "repo": "owner/repo",
            "base_commit": "a" * 40,
        },
        dest,
    )
    assert result["ready"] is True
    assert result["status"] == "already_materialized"


def test_materialize_source_falls_back_after_git_fetch_failure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "evals.e1c_strict_v5_postfreeze._run",
        lambda args, **kwargs: {"exit_code": 0, "stdout": "", "stderr": "", "timed_out": False}
        if args[:2] in (["git", "init"], ["git", "remote"])
        else {"exit_code": 128, "stdout": "", "stderr": "network", "timed_out": False},
    )
    monkeypatch.setattr(
        "evals.e1c_strict_v5_postfreeze._github_archive",
        lambda repo, base_commit, destination: {
            "ready": True,
            "status": "github_archive_materialized",
            "head": base_commit,
        },
    )
    result = materialize_source(
        {"repo": "owner/repo", "base_commit": "b" * 40},
        tmp_path / "source",
    )
    assert result["ready"] is True
    assert result["status"] == "github_archive_materialized"
    assert result["git_fetch_status"] == "failed_then_github_archive_fallback"
