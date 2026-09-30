import json

from evals.e1c_strict_v6_reserve import freeze


def _row(instance_id: str, digit: str) -> dict:
    return {
        "instance_id": instance_id,
        "repo": "owner/repo",
        "base_commit": digit * 40,
        "image": f"swebench/{instance_id}:latest",
    }


def test_v6_freeze_requires_prereg_and_is_deterministic(tmp_path, monkeypatch) -> None:
    prereg = tmp_path / "data" / "e1c_strict_v6_prereg.json"
    prereg.parent.mkdir()
    prereg.write_text(json.dumps({"schema": "test"}), encoding="utf-8")
    monkeypatch.setattr("evals.e1c_strict_v6_reserve.ROOT", tmp_path)
    monkeypatch.setattr("evals.e1c_strict_v6_reserve.denylist", lambda: frozenset())
    rows = [_row("a", "a"), _row("b", "b"), _row("c", "c"), _row("d", "d")]
    left = freeze(rows, source_revision="rev", output=tmp_path / "left.json")
    right = freeze(list(reversed(rows)), source_revision="rev", output=tmp_path / "right.json")
    assert left["instance_ids"] == right["instance_ids"]
    assert left["provider_calls"] == 0
