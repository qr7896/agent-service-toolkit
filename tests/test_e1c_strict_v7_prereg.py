import json

from evals.e1c_strict_v7_prereg import build


def test_v7_prereg_pins_mechanism_before_canary_selection(tmp_path, monkeypatch) -> None:
    boundary = tmp_path / "boundary.json"
    boundary.write_text(json.dumps({"canary_selected": False}), encoding="utf-8")
    files = []
    for index in range(3):
        path = tmp_path / f"mechanism_{index}.py"
        path.write_text(f"VALUE = {index}\n", encoding="utf-8")
        files.append(path)
    monkeypatch.setattr("evals.e1c_strict_v7_prereg.ROOT", tmp_path)
    monkeypatch.setattr("evals.e1c_strict_v7_prereg.BOUNDARY", boundary)
    monkeypatch.setattr("evals.e1c_strict_v7_prereg.MECHANISM_FILES", tuple(files))
    result = build()
    assert result["canary_selected_at_freeze"] is False
    assert result["provider_calls"] == 0
    assert len(result["mechanism_sha256"]) == 64
    assert result["development_replay_is_independent_evidence"] is False
