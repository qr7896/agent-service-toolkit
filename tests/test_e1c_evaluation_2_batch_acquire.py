from types import SimpleNamespace

import pytest

from evals import e1c_evaluation_2_batch_acquire as batch


def test_batch_disk_gate_stops_before_transfer(tmp_path, monkeypatch):
    row = {"instance_id": "marshmallow-code__marshmallow-1252", "official": {"compressed_layer_bytes": 1024**3}}
    monkeypatch.setattr(batch, "frozen_rows", lambda: [row])
    monkeypatch.setattr(batch.shutil, "disk_usage", lambda path: SimpleNamespace(free=21 * 1024**3))
    monkeypatch.setattr(batch, "build_layout", lambda *args, **kwargs: pytest.fail("transfer must not start"))
    with pytest.raises(RuntimeError, match="disk stop gate"):
        batch.acquire_all(tmp_path)


def test_verified_cleanup_is_task_local(tmp_path):
    root = tmp_path / "acquire"
    workdir = root / "task-1"
    layout = workdir / "layout"
    layout.mkdir(parents=True)
    (layout / "blob").write_bytes(b"generated")
    (workdir / "docker_archive.tar").write_bytes(b"generated")
    (workdir / "loaded.json").write_text("verified", encoding="utf-8")
    batch._cleanup_verified_temporary(workdir, root)
    assert not layout.exists()
    assert not (workdir / "docker_archive.tar").exists()
    assert (workdir / "loaded.json").read_text(encoding="utf-8") == "verified"
    with pytest.raises(ValueError, match="escapes acquisition root"):
        batch._cleanup_verified_temporary(tmp_path / "other", root)
