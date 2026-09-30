import hashlib
import json

from evals.e1c_strict_v7_selection_boundary import build


def test_v7_boundary_adds_v6_canary_to_prior_contamination(tmp_path, monkeypatch) -> None:
    identities = [f"task-{index:03d}" for index in range(244)]
    ledger = tmp_path / "ledger.json"
    ledger.write_text(
        json.dumps(
            {
                "identities": identities,
                "identity_sha256": hashlib.sha256(
                    json.dumps(identities, separators=(",", ":")).encode()
                ).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    manifest = tmp_path / "v6.json"
    manifest.write_text(
        json.dumps(
            {
                "tasks": [
                    {"instance_id": "v6-a"},
                    {"instance_id": "v6-b"},
                    {"instance_id": "v6-c"},
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("evals.e1c_strict_v7_selection_boundary.LEDGER", ledger)
    monkeypatch.setattr("evals.e1c_strict_v7_selection_boundary.V6_MANIFEST", manifest)
    result = build()
    assert result["contamination_count"] == 247
    assert result["explicit_v6_exclusions"] == ["v6-a", "v6-b", "v6-c"]
    assert result["canary_selected"] is False
    assert result["mechanism_must_be_frozen_before_canary_selection"] is True
    assert result["provider_calls"] == 0


def test_v7_boundary_deduplicates_already_contaminated_v6_identity(
    tmp_path, monkeypatch
) -> None:
    identities = [f"task-{index:03d}" for index in range(244)] + ["v6-a"]
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps({"identities": identities}), encoding="utf-8")
    manifest = tmp_path / "v6.json"
    manifest.write_text(
        json.dumps(
            {
                "tasks": [
                    {"instance_id": "v6-a"},
                    {"instance_id": "v6-b"},
                    {"instance_id": "v6-c"},
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("evals.e1c_strict_v7_selection_boundary.LEDGER", ledger)
    monkeypatch.setattr("evals.e1c_strict_v7_selection_boundary.V6_MANIFEST", manifest)
    result = build()
    assert result["contamination_count"] == 247
