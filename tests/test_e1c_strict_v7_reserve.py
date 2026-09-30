import json

from evals.e1c_strict_v7_reserve import freeze


def _row(instance_id: str, digit: str) -> dict:
    return {
        "instance_id": instance_id,
        "repo": "owner/repo",
        "base_commit": digit * 40,
        "image": f"swebench/{instance_id}:latest",
    }


def test_v7_reserve_is_deterministic_and_excludes_touched(tmp_path, monkeypatch) -> None:
    prereg = tmp_path / "prereg.json"
    prereg.write_text(
        json.dumps(
            {
                "selection_salt": "e1c-strict-v7-independent-canary",
                "canary_selected_at_freeze": False,
                "prereg_sha256": "a" * 64,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("evals.e1c_strict_v7_reserve.PREREG", prereg)
    monkeypatch.setattr("evals.e1c_strict_v7_reserve.denylist", lambda: frozenset({"a"}))
    rows = [_row("a", "a"), _row("b", "b"), _row("c", "c"), _row("d", "d"), _row("e", "e")]
    left = freeze(rows, source_revision="rev", output=tmp_path / "left.json")
    right = freeze(list(reversed(rows)), source_revision="rev", output=tmp_path / "right.json")
    assert left["instance_ids"] == right["instance_ids"]
    assert "a" not in left["instance_ids"]
    assert left["provider_calls"] == 0
