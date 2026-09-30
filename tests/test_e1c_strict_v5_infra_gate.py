import json

import evals.e1c_strict_v5_infra_gate as gate


def _write(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_gate_closes_mirror_on_any_authoritative_digest_mismatch(
    tmp_path, monkeypatch
) -> None:
    identity = tmp_path / "identity.json"
    transport = tmp_path / "transport.json"
    trend = tmp_path / "trend.json"
    cache_budget = tmp_path / "cache_budget.json"
    _write(
        identity,
        {
            "authoritative_ready_count": 2,
            "mirror_equivalent_count": 0,
            "mirror_transport_ready": False,
            "rows": [
                {
                    "instance_id": "a__one",
                    "authoritative_digest": "sha256:" + "a" * 64,
                    "mirror_digest": "sha256:" + "b" * 64,
                },
                {
                    "instance_id": "b__two",
                    "authoritative_digest": None,
                    "mirror_digest": "sha256:" + "c" * 64,
                },
            ],
        },
    )
    _write(
        transport,
        {
            "ready": False,
            "reason": "blob_transport_gate_incomplete",
            "checked_count": 1,
        },
    )
    _write(
        trend,
        {
            "state": "repeated_bounded_transport_error",
            "recheck_information_gain_likely": False,
            "diagnostic_only": True,
            "changes_admission_gate": False,
        },
    )
    _write(
        cache_budget,
        {
            "diagnostic_only": True,
            "changes_admission_gate": False,
            "minimum_required_bytes_per_second_for_all_missing_images": 1544201,
            "minimum_required_megabytes_per_second_for_all_missing_images": 1.544,
        },
    )
    monkeypatch.setattr(gate, "IDENTITY", identity)
    monkeypatch.setattr(gate, "BLOB_PREFLIGHT", transport)
    monkeypatch.setattr(gate, "TRANSPORT_TREND", trend)
    monkeypatch.setattr(gate, "CACHE_BUDGET", cache_budget)
    monkeypatch.setattr(
        gate,
        "inspect_local_images",
        lambda: {"ready": False, "missing_instance_ids": ["a__one", "b__two"]},
    )
    result = gate.build(output=tmp_path / "out.json")
    assert result["ready"] is False
    assert result["full_pull_allowed"] is False
    assert result["mirror_route_conclusively_closed"] is True
    assert result["mirror_mismatch_instance_ids"] == ["a__one"]
    assert result["next_action"] == "bounded_transport_preflight_only"
    assert result["transport_trend_state"] == "repeated_bounded_transport_error"
    assert result["transport_recheck_information_gain_likely"] is False
    assert result["transport_trend_changes_admission_gate"] is False
    assert result["cache_budget_diagnostic_only"] is True
    assert result["cache_budget_changes_admission_gate"] is False
    assert result["cache_budget_minimum_required_bytes_per_second"] == 1544201


def test_gate_allows_advance_only_after_budget_preflight(tmp_path, monkeypatch) -> None:
    identity = tmp_path / "identity.json"
    transport = tmp_path / "transport.json"
    trend = tmp_path / "trend.json"
    cache_budget = tmp_path / "cache_budget.json"
    _write(identity, {"rows": [], "mirror_transport_ready": False})
    _write(trend, {})
    _write(cache_budget, {})
    _write(
        transport,
        {
            "ready": True,
            "reason": "all_frozen_blob_transports_ready",
            "checked_count": 3,
        },
    )
    monkeypatch.setattr(gate, "IDENTITY", identity)
    monkeypatch.setattr(gate, "BLOB_PREFLIGHT", transport)
    monkeypatch.setattr(gate, "TRANSPORT_TREND", trend)
    monkeypatch.setattr(gate, "CACHE_BUDGET", cache_budget)
    monkeypatch.setattr(
        gate,
        "inspect_local_images",
        lambda: {"ready": False, "missing_instance_ids": ["a__one"]},
    )
    result = gate.build(output=tmp_path / "out.json")
    assert result["full_pull_allowed"] is True
    assert result["next_action"] == "advance_admission"
    assert result["ready"] is False


def test_gate_prefers_local_images_without_network(tmp_path, monkeypatch) -> None:
    identity = tmp_path / "identity.json"
    transport = tmp_path / "transport.json"
    trend = tmp_path / "trend.json"
    cache_budget = tmp_path / "cache_budget.json"
    _write(identity, {"rows": []})
    _write(transport, {"ready": False})
    _write(trend, {})
    _write(cache_budget, {})
    monkeypatch.setattr(gate, "IDENTITY", identity)
    monkeypatch.setattr(gate, "BLOB_PREFLIGHT", transport)
    monkeypatch.setattr(gate, "TRANSPORT_TREND", trend)
    monkeypatch.setattr(gate, "CACHE_BUDGET", cache_budget)
    monkeypatch.setattr(
        gate,
        "inspect_local_images",
        lambda: {"ready": True, "missing_instance_ids": []},
    )
    result = gate.build(output=tmp_path / "out.json")
    assert result["ready"] is True
    assert result["full_pull_allowed"] is False
    assert result["next_action"] == "resume_admission"
    assert result["c5_allowed"] is False
    assert result["fresh30_allowed"] is False
