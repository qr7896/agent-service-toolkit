import json

import pytest

from evals import e1c_evaluation_2_traceback_gold as gold


def test_gold_refuses_nonrepeated_public_exception(tmp_path, monkeypatch):
    pilot = tmp_path / "pilot"
    pilot.mkdir()
    (pilot / "freeze.json").write_text('{"instance_id":"repo__task"}', encoding="utf-8")
    base_dir = tmp_path / "base" / "repo__task"
    base_dir.mkdir(parents=True)
    (base_dir / "result.json").write_text(json.dumps({
        "schema": "e1c2-dev-traceback-replay-v1", "provider_calls": 0,
        "replacement_quote": "AttributeError: expected",
        "execution": {"network_none": True, "pull_never": True,
                      "repeatable_nonsetup_failure": False, "runs": []},
    }), encoding="utf-8")
    monkeypatch.setattr(gold, "PILOT", pilot)
    monkeypatch.setattr(gold, "BASE", tmp_path / "base")
    with pytest.raises(ValueError, match="no repeated exact public exception"):
        gold.run()
