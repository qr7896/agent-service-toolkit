import json

from evals.v3_prospective_readiness import build_readiness, main, validate_row


def _row():
    return {
        "id": "t1",
        "ended_at": "2026-09-19T00:00:00+00:00",
        "source_repo": "repo",
        "source_commit_at_execution": "abc",
        "task": "fix route",
        "changed_paths": [],
        "status": "succeeded",
        "experience_hits": [],
        "experience_ids": [],
        "adopted_experience_ids": None,
        "adoption_observed": False,
    }


def test_prospective_row_is_ready_with_execution_provenance():
    assert validate_row(_row()) == []
    assert build_readiness([_row()])["ready"] is True


def test_prospective_readiness_fails_closed_for_missing_commit():
    row = _row()
    row["source_commit_at_execution"] = ""
    artifact = build_readiness([row])
    assert artifact["ready"] is False
    assert "missing:source_commit_at_execution" in artifact["details"][0]["errors"]


def test_usage_feedback_requires_event_time():
    row = _row()
    row["usage_feedback"] = [{"helped": True}]
    assert "invalid:untimestamped_usage_feedback" in validate_row(row)


def test_readiness_manifest_keeps_eligible_and_blocked_rows_separate():
    good = _row()
    bad = {**_row(), "id": "bad", "source_commit_at_execution": ""}
    artifact = build_readiness([good, bad])
    assert artifact["ready_ids"] == ["t1"]
    assert artifact["blocked_ids"] == ["bad"]
    assert [row["id"] for row in artifact["eligible_rows"]] == ["t1"]
    assert artifact["blocked_rows_detail"][0]["row"]["id"] == "bad"


def test_readiness_cli_does_not_modify_source(tmp_path, monkeypatch):
    source = tmp_path / "rows.jsonl"
    output = tmp_path / "manifest.json"
    source.write_text(json.dumps(_row()) + "\n", encoding="utf-8")
    before = source.read_bytes()
    monkeypatch.setattr(
        "sys.argv",
        ["v3_prospective_readiness", "--trajectories", str(source), "--output", str(output)],
    )
    main()
    assert source.read_bytes() == before
    assert json.loads(output.read_text(encoding="utf-8"))["ready"] is True


def test_adoption_observation_invariants():
    row = _row()
    row["adoption_observed"] = False
    row["adopted_experience_ids"] = []
    assert "invalid:unobserved_adoption_must_be_null" in validate_row(row)
    row["adoption_observed"] = True
    row["experience_ids"] = ["a"]
    row["adopted_experience_ids"] = ["b"]
    assert "invalid:adopted_not_retrieved" in validate_row(row)
