import evals.e1c_strict_v5_advance_admission as advance


def test_advance_stops_at_image_gate(monkeypatch) -> None:
    monkeypatch.setattr(
        advance,
        "inspect_local_images",
        lambda: {"ready": False, "missing_instance_ids": ["a__one"]},
    )
    monkeypatch.setattr(
        advance,
        "run_blob_preflight",
        lambda proxy=None, max_estimated_seconds=None: {"ready": True, "checked_count": 1, "required_count": 1},
    )
    monkeypatch.setattr(
        advance,
        "acquire",
        lambda pull_timeout: {"ready": False, "reason": "official_manifest_preflight_incomplete"},
    )
    monkeypatch.setattr(
        advance,
        "build_image_identity",
        lambda proxy=None: {
            "mirror_transport_ready": False,
            "authoritative_ready_count": 0,
            "mirror_equivalent_count": 0,
            "mirror_mismatch_count": 0,
            "mirror_route_conclusively_closed": False,
        },
    )
    monkeypatch.setattr(
        advance,
        "resume_admission",
        lambda: (_ for _ in ()).throw(AssertionError("resume must not run")),
    )
    result = advance.run()
    assert result["ready"] is False
    assert result["stage"] == "image_identity"
    assert result["provider_calls"] == 0


def test_advance_reaches_admission_when_images_ready(monkeypatch) -> None:
    monkeypatch.setattr(
        advance,
        "inspect_local_images",
        lambda: {"ready": True, "missing_instance_ids": []},
    )
    monkeypatch.setattr(
        advance,
        "acquire",
        lambda pull_timeout: (_ for _ in ()).throw(AssertionError("acquire must not run")),
    )
    monkeypatch.setattr(
        advance,
        "resume_admission",
        lambda: {"ready": True, "reason": "strict_v5_admission_ready"},
    )
    result = advance.run()
    assert result["ready"] is True
    assert result["stage"] == "admission_seal"
    assert result["reason"] == "strict_v5_admission_ready"


def test_advance_uses_mirror_only_after_digest_equivalence(monkeypatch) -> None:
    monkeypatch.setattr(
        advance,
        "inspect_local_images",
        lambda: {"ready": False, "missing_instance_ids": ["a__one"]},
    )
    monkeypatch.setattr(
        advance,
        "run_blob_preflight",
        lambda proxy=None, max_estimated_seconds=None: {"ready": True, "checked_count": 1, "required_count": 1},
    )
    monkeypatch.setattr(
        advance,
        "acquire",
        lambda pull_timeout: {
            "ready": False,
            "reason": "official_manifest_preflight_incomplete",
        },
    )
    identity = {
        "mirror_transport_ready": True,
        "authoritative_ready_count": 2,
        "mirror_equivalent_count": 2,
    }
    monkeypatch.setattr(
        advance,
        "build_image_identity",
        lambda proxy=None: identity,
    )
    monkeypatch.setattr(
        advance,
        "acquire_equivalent_mirror",
        lambda payload, pull_timeout: {
            "ready": True,
            "reason": "equivalent_mirror_images_digest_verified",
        },
    )
    monkeypatch.setattr(
        advance,
        "resume_admission",
        lambda: {"ready": True, "reason": "strict_v5_admission_ready"},
    )
    result = advance.run()
    assert result["ready"] is True
    assert result["stage"] == "admission_seal"


def test_advance_passes_proxy_into_identity_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        advance,
        "inspect_local_images",
        lambda: {"ready": False, "missing_instance_ids": ["a__one"]},
    )
    monkeypatch.setattr(
        advance,
        "run_blob_preflight",
        lambda proxy=None, max_estimated_seconds=None: {
            "ready": True,
            "checked_count": 1,
            "required_count": 1,
        },
    )
    monkeypatch.setattr(
        advance,
        "acquire",
        lambda pull_timeout: {"ready": False, "reason": "pull_failed"},
    )
    seen = {}

    def fake_identity(proxy=None):
        seen["proxy"] = proxy
        return {
            "mirror_transport_ready": False,
            "authoritative_ready_count": 2,
            "mirror_equivalent_count": 0,
            "mirror_mismatch_count": 2,
            "mirror_route_conclusively_closed": True,
        }

    monkeypatch.setattr(advance, "build_image_identity", fake_identity)
    result = advance.run(proxy="http://127.0.0.1:7892")
    assert seen["proxy"] == "http://127.0.0.1:7892"
    assert result["stage"] == "image_identity"
    assert result["mirror_mismatch_count"] == 2
    assert result["mirror_route_conclusively_closed"] is True


def test_explicit_proxy_is_scoped_and_not_serialized(monkeypatch) -> None:
    monkeypatch.delenv("HTTP_PROXY", raising=False)
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    monkeypatch.delenv("http_proxy", raising=False)
    monkeypatch.delenv("https_proxy", raising=False)
    seen = {}

    def fake_run(pull_timeout, proxy):
        import os

        seen["http"] = os.environ.get("HTTP_PROXY")
        seen["https"] = os.environ.get("HTTPS_PROXY")
        return {
            "schema": "e1c-strict-v5-advance-admission-v1",
            "ready": False,
            "stage": "image_identity",
            "reason": "blocked",
            "provider_calls": 0,
            "live_model_run": False,
        }

    monkeypatch.setattr(advance, "_run", fake_run)
    result = advance.run(proxy="http://127.0.0.1:7892")
    assert seen == {
        "http": "http://127.0.0.1:7892",
        "https": "http://127.0.0.1:7892",
    }
    assert result["network_exit"] == {
        "explicit_proxy": True,
        "proxy_value_recorded": False,
    }
    import os

    assert os.environ.get("HTTP_PROXY") is None
    assert os.environ.get("HTTPS_PROXY") is None


def test_advance_stops_before_pull_when_blob_transport_is_slow(monkeypatch) -> None:
    monkeypatch.setattr(
        advance,
        "inspect_local_images",
        lambda: {"ready": False, "missing_instance_ids": ["a__one"]},
    )
    monkeypatch.setattr(
        advance,
        "run_blob_preflight",
        lambda proxy=None, max_estimated_seconds=None: {
            "ready": False,
            "reason": "blob_transport_gate_incomplete",
            "checked_count": 1,
            "required_count": 3,
        },
    )
    monkeypatch.setattr(
        advance,
        "acquire",
        lambda pull_timeout: (_ for _ in ()).throw(AssertionError("pull path must not run")),
    )
    result = advance.run(proxy="http://127.0.0.1:7892")
    assert result["ready"] is False
    assert result["stage"] == "blob_transport_preflight"
    assert result["missing_instance_ids"] == ["a__one"]
