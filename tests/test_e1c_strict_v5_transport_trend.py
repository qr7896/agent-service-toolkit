import json

import evals.e1c_strict_v5_transport_trend as trend


def _write_ledger(path, entries):
    path.write_text(
        "".join(json.dumps(entry) + "\n" for entry in entries),
        encoding="utf-8",
    )


def _entry(row):
    return {
        "ready": bool(row.get("ready")),
        "rows": [row],
        "provider_calls": 0,
        "live_model_run": False,
    }


def test_repeated_errors_are_advisory_not_admission_gate(tmp_path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    _write_ledger(
        ledger,
        [
            _entry(
                {
                    "instance_id": "x__1",
                    "ready": False,
                    "reason": "blob_preflight_error",
                    "error_sha256": "a" * 64,
                }
            ),
            _entry(
                {
                    "instance_id": "x__1",
                    "ready": False,
                    "reason": "blob_preflight_error",
                    "error_sha256": "b" * 64,
                }
            ),
        ],
    )
    result = trend.build(output=tmp_path / "out.json", ledger=ledger)
    assert result["state"] == "repeated_bounded_transport_error"
    assert result["recheck_information_gain_likely"] is False
    assert result["diagnostic_only"] is True
    assert result["changes_admission_gate"] is False
    assert result["c5_allowed"] is False


def test_budget_compatible_observation_is_reported_without_opening_gate(
    tmp_path,
) -> None:
    ledger = tmp_path / "ledger.jsonl"
    _write_ledger(
        ledger,
        [
            _entry(
                {
                    "instance_id": "x__1",
                    "ready": True,
                    "reason": "blob_transport_ready",
                    "estimated_full_image_seconds": 850.0,
                }
            )
        ],
    )
    result = trend.build(
        output=tmp_path / "out.json",
        ledger=ledger,
        pull_timeout=900,
    )
    assert result["state"] == "budget_compatible_observed"
    assert result["recheck_information_gain_likely"] is True
    assert result["changes_admission_gate"] is False
    assert result["formal_admission_source"] == "e1c_strict_v5_blob_preflight"


def test_partial_progress_is_structured_when_available(tmp_path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    _write_ledger(
        ledger,
        [
            _entry(
                {
                    "instance_id": "x__1",
                    "ready": False,
                    "reason": "blob_preflight_error",
                    "partial_bytes_received": 262144,
                    "requested_bytes": 1048576,
                }
            )
        ],
    )
    result = trend.build(output=tmp_path / "out.json", ledger=ledger)
    assert result["partial_progress_observation_count"] == 1
    assert result["latest_partial_ratio"] == 0.25
    assert result["best_partial_ratio"] == 0.25
