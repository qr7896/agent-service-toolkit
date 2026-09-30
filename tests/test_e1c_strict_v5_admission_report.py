from pathlib import Path

from evals.e1c_strict_v5_admission_report import _image_ready, _load_optional


def test_load_optional_fails_closed_on_missing_or_bad_json(tmp_path: Path) -> None:
    assert _load_optional(tmp_path / "missing.json") == {}
    bad = tmp_path / "bad.json"
    bad.write_text("{bad", encoding="utf-8")
    assert _load_optional(bad) == {}


def test_image_ready_accepts_verified_local_digest() -> None:
    assert _image_ready({"ready": False}, {"image_digest": "repo@sha256:" + "a" * 64}) is True
    assert _image_ready({"ready": False}, {"image_digest": None}) is False
