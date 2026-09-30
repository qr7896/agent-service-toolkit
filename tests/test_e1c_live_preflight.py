import json

import pytest

from evals import e1c_live_preflight as live


def test_final_cohort_source_lookup_includes_replacements(tmp_path, monkeypatch):
    monkeypatch.setattr(live, "OUT", tmp_path)
    (tmp_path / "source_inventory.json").write_text(
        json.dumps({"tasks": [{"instance_id": "original"}]}), encoding="utf-8"
    )
    replacement = tmp_path / "replacement_source_inventory.json"
    replacement.write_text(
        json.dumps({"tasks": [{"instance_id": "replacement"}]}), encoding="utf-8"
    )
    assert set(live.source_rows()) == {"original", "replacement"}
    replacement.write_text(
        json.dumps({"tasks": [{"instance_id": "original"}]}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="duplicate source identity"):
        live.source_rows()
