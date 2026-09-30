import json
from evals.e1c_strict_v8_prereg import build

def test_v8_prereg_pins_mechanism_before_canary_selection(tmp_path, monkeypatch):
    boundary = tmp_path / "boundary.json"
    boundary.write_text(json.dumps({"canary_selected": False}), encoding="utf-8")
    files=[]
    for i in range(2):
        p=tmp_path/f"m{i}.py"; p.write_text(f"X={i}\n", encoding="utf-8"); files.append(p)
    monkeypatch.setattr("evals.e1c_strict_v8_prereg.ROOT", tmp_path)
    monkeypatch.setattr("evals.e1c_strict_v8_prereg.BOUNDARY", boundary)
    monkeypatch.setattr("evals.e1c_strict_v8_prereg.MECHANISM_FILES", tuple(files))
    result=build()
    assert result["provider_calls"] == 0
    assert result["canary_selected_at_freeze"] is False
    assert result["development_replay_is_independent_evidence"] is False
