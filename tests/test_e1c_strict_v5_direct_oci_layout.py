import evals.e1c_strict_v5_direct_oci_layout as layout


def test_linux_amd64_descriptor_selects_exact_platform() -> None:
    payload = {
        "manifests": [
            {
                "digest": "sha256:" + "a" * 64,
                "platform": {"os": "linux", "architecture": "amd64"},
            },
            {
                "digest": "sha256:" + "b" * 64,
                "platform": {"os": "linux", "architecture": "arm64"},
            },
        ]
    }
    assert layout._linux_amd64_descriptor(payload)["digest"] == "sha256:" + "a" * 64


def test_write_verified_bytes_rejects_wrong_digest(tmp_path) -> None:
    try:
        layout._write_verified_bytes(tmp_path, "sha256:" + "0" * 64, b"x")
    except RuntimeError as exc:
        assert str(exc) == "descriptor_digest_mismatch"
    else:
        raise AssertionError("expected digest mismatch")


def test_remaining_uses_single_total_deadline(monkeypatch) -> None:
    monkeypatch.setattr(layout.time, "monotonic", lambda: 150.0)
    assert layout._remaining(100.0, 900) == 850
