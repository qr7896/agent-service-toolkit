import json

from evals.e1c_strict_v8_selection_boundary import build


def test_v8_boundary_excludes_v6_and_v7_and_selects_nothing(tmp_path, monkeypatch) -> None:
    base = [f"task-{index:03d}" for index in range(244)]
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps({"identities": base}), encoding="utf-8")
    v6 = tmp_path / "v6.json"
    v7 = tmp_path / "v7.json"
    v6.write_text(json.dumps({"tasks": [{"instance_id": x} for x in ("v6-a", "v6-b", "v6-c")]}), encoding="utf-8")
    v7.write_text(json.dumps({"tasks": [{"instance_id": x} for x in ("v7-a", "v7-b", "v7-c")]}), encoding="utf-8")
    seal = tmp_path / "seal.json"
    seal.write_text(json.dumps({"decision": "seal_without_image_or_live"}), encoding="utf-8")
    monkeypatch.setattr("evals.e1c_strict_v8_selection_boundary.BASE_LEDGER", ledger)
    monkeypatch.setattr("evals.e1c_strict_v8_selection_boundary.V6_MANIFEST", v6)
    monkeypatch.setattr("evals.e1c_strict_v8_selection_boundary.V7_MANIFEST", v7)
    monkeypatch.setattr("evals.e1c_strict_v8_selection_boundary.V7_SEAL", seal)
    result = build()
    assert result["contamination_count"] == 250
    assert result["canary_selected"] is False
    assert result["mechanism_must_be_frozen_before_canary_selection"] is True
    assert result["explicit_prior_canary_exclusions"] == ["v6-a", "v6-b", "v6-c", "v7-a", "v7-b", "v7-c"]
