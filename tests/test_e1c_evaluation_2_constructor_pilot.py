import asyncio
import json

import pytest

from evals import e1c_evaluation_2_constructor_pilot as pilot


def test_constructor_selection_uses_public_issue_only(tmp_path, monkeypatch):
    issue = tmp_path / "repo__one"
    issue.mkdir()
    (issue / "frozen_input_v3.json").write_text(json.dumps({
        "schema": "e1c-evaluation-2-probe-input-v3", "status": "ready_for_generation",
        "issue": "Please expose `flag` in `Widget.__init__()`, default `False`.",
    }), encoding="utf-8")
    monkeypatch.setattr(pilot, "ISSUE", tmp_path)
    path, _, quote = pilot._selected()
    assert path.parent.name == "repo__one"
    assert quote == "expose `flag` in `Widget.__init__()`, default `False`"


def test_constructor_pilot_never_restarts_existing_state(tmp_path, monkeypatch):
    frozen = {"run_id": pilot.RUN_ID}
    freeze_path = tmp_path / "freeze.json"
    freeze_path.write_text(json.dumps(frozen), encoding="utf-8")
    (tmp_path / "state.json").write_text('{"status":"interrupted_no_auto_retry"}', encoding="utf-8")
    monkeypatch.setattr(pilot, "FREEZE", freeze_path)
    monkeypatch.setattr(pilot, "OUT", tmp_path)
    monkeypatch.setattr(pilot, "LEDGER", tmp_path / "provider_calls.jsonl")
    monkeypatch.setattr(pilot, "preflight", lambda: frozen)
    with pytest.raises(FileExistsError, match="never auto-retry"):
        asyncio.run(pilot.run())
