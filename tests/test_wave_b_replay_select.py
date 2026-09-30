from __future__ import annotations

from scripts.wave_b_replay_select import excluded


def test_excluded_accepts_short_or_full_prefix() -> None:
    full = "abcdef1234567890"
    assert excluded(full, {"abcdef1"})
    assert excluded("abcdef1", {full})
    assert not excluded(full, {"1234567"})
