import asyncio
import json
import subprocess

import pytest

from evals import e1c_evaluation_2_traceback_pilot as pilot


def test_traceback_pilot_selects_public_issue_and_sizes_elastic_budget(tmp_path, monkeypatch):
    issue = tmp_path / "issue" / "repo__task"
    issue.mkdir(parents=True)
    (issue / "frozen_input_v3.json").write_text(json.dumps({
        "schema": "e1c-evaluation-2-probe-input-v3", "status": "ready_for_generation",
        "issue": "Traceback:\nAttributeError: missing attribute",
    }), encoding="utf-8")
    other = tmp_path / "issue" / "repo__other"
    other.mkdir()
    (other / "frozen_input_v3.json").write_text(json.dumps({
        "schema": "e1c-evaluation-2-probe-input-v3", "status": "ready_for_generation",
        "issue": "Improve documentation",
    }), encoding="utf-8")
    admission = tmp_path / "admission" / "repo__task"
    admission.mkdir(parents=True)
    for phase in ("base", "gold"):
        (admission / f"{phase}.json").write_text(
            '{"phase_pass": true, "provider_calls": 0}', encoding="utf-8",
        )
    monkeypatch.setattr(pilot, "ISSUE", tmp_path / "issue")
    monkeypatch.setattr(pilot, "ADMISSION", tmp_path / "admission")
    monkeypatch.setattr(pilot, "_prompt", lambda _: "public issue and production source only")
    monkeypatch.setattr(pilot, "estimate_tokens", lambda _: 3000)
    monkeypatch.setattr(pilot, "verified_local_image", lambda _: "sha256:" + "a" * 64)
    monkeypatch.setattr(pilot.subprocess, "run", lambda *_, **__: subprocess.CompletedProcess([], 0, "sha256:" + "a" * 64, ""))

    frozen = pilot.preflight()
    assert frozen["instance_id"] == "repo__task"
    assert frozen["estimated_call_reserve"] == 5400
    assert frozen["elastic_provider_ceiling"] == 8100
    assert frozen["hard_provider_token_cap"] == 12000

    monkeypatch.setattr(pilot, "MAX_PROVIDER_TOKENS", 5000)
    with pytest.raises(ValueError, match="reserve 5400 exceeds frozen ceiling 5000"):
        pilot.preflight()


def test_traceback_pilot_never_restarts_existing_state(tmp_path, monkeypatch):
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
