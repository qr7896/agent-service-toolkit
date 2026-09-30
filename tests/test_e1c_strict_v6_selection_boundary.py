import hashlib
import json

from evals.e1c_strict_v6_selection_boundary import build


def test_selection_boundary_pins_ledger(tmp_path, monkeypatch) -> None:
    identities = [f"task-{i:03d}" for i in range(244)]
    identity_sha = hashlib.sha256(
        json.dumps(identities, separators=(",", ":")).encode()
    ).hexdigest()
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps({
        "identities": identities,
        "identity_sha256": identity_sha,
    }), encoding="utf-8")
    monkeypatch.setattr(
        "evals.e1c_strict_v6_selection_boundary.LEDGER",
        ledger,
    )
    result = build()
    assert result["contamination_count"] == 244
    assert result["contamination_identity_sha256"] == identity_sha
    assert result["provider_calls"] == 0
