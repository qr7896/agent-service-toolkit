import asyncio
import json

import pytest

from evals import e1c_evaluation_2_feedback_pilot as pilot


def test_feedback_pilot_never_restarts_existing_provider_state(tmp_path, monkeypatch):
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
