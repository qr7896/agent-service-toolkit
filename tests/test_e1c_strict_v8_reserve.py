import json
from evals.e1c_strict_v8_reserve import freeze

def row(i, digit):
    return {"instance_id": i, "repo":"o/r", "base_commit":digit*40, "image":f"img:{i}"}

def test_v8_reserve_is_deterministic_and_excludes_prior(tmp_path, monkeypatch):
    prereg=tmp_path/"prereg.json"
    prereg.write_text(json.dumps({"selection_salt":"e1c-strict-v8-independent-canary","canary_selected_at_freeze":False,"prereg_sha256":"a"*64}), encoding="utf-8")
    monkeypatch.setattr("evals.e1c_strict_v8_reserve.PREREG", prereg)
    monkeypatch.setattr("evals.e1c_strict_v8_reserve.denylist", lambda: frozenset({"a"}))
    rows=[row("a","a"),row("b","b"),row("c","c"),row("d","d"),row("e","e")]
    left=freeze(rows, source_revision="rev", output=tmp_path/"l.json")
    right=freeze(list(reversed(rows)), source_revision="rev", output=tmp_path/"r.json")
    assert left["instance_ids"] == right["instance_ids"]
    assert "a" not in left["instance_ids"]
