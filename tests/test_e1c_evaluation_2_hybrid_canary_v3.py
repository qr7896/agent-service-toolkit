import json

import pytest

from evals import e1c_evaluation_2_hybrid_canary_v3 as canary


def test_freeze_precedes_selection_and_forbids_refreeze(tmp_path, monkeypatch):
    monkeypatch.setattr(canary, "FREEZE", tmp_path / "freeze.json")
    monkeypatch.setattr(canary, "IDENTITY", tmp_path / "identity.json")
    monkeypatch.setattr(canary, "method", lambda: {"max_requests": 6, "batch_provider_token_cap": 60000})
    with pytest.raises(FileNotFoundError):
        canary.checked_method()
    assert canary.freeze_method()["batch_provider_token_cap"] == 60000
    canary.IDENTITY.write_bytes(b"{}")
    with pytest.raises(FileExistsError):
        canary.freeze_method()


def test_cached_transport_never_requests_network_and_binds_method(tmp_path, monkeypatch):
    identity, metadata, transport, freeze = [tmp_path / name for name in ("identity", "metadata", "transport", "freeze")]
    identity.write_bytes(b'{"tasks":[{"instance_id":"repo__repo-1"}]}')
    metadata.write_bytes(json.dumps({"identity_sha256": canary._sha(identity), "tasks": [{"instance_id": "repo__repo-1"}]}).encode())
    freeze.write_bytes(b"frozen method")
    monkeypatch.setattr(canary, "IDENTITY", identity)
    monkeypatch.setattr(canary, "FREEZE", freeze)
    monkeypatch.setattr(canary.stage, "METADATA", metadata)
    monkeypatch.setattr(canary.stage, "TRANSPORT", transport)
    monkeypatch.setattr(canary, "MetadataClient", lambda: pytest.fail("cached download must not call metadata network"))
    value = {"identity_sha256": canary._sha(identity), "metadata_sha256": canary._sha(metadata), "method_freeze_sha256": canary._sha(freeze)}
    transport.write_bytes(json.dumps(value).encode())
    assert canary.audit_transport() == value
    freeze.write_bytes(b"changed")
    with pytest.raises(ValueError, match="binding"):
        canary.audit_transport()


def test_live_binding_uses_canary_inputs_budget_and_fixed_denominator(tmp_path, monkeypatch):
    monkeypatch.setattr(canary, "OUT", tmp_path)
    monkeypatch.setattr(canary, "bind_stages", lambda: None)
    runtime = canary.controller.runtime
    for name in ("OUT", "PROTOCOL", "IDENTITY", "FIXED_DENOMINATOR", "TASK_CAP", "BATCH_CAP", "OUTPUT_CAP", "inputs", "preflight", "execute_role"):
        monkeypatch.setattr(runtime, name, getattr(runtime, name))
    monkeypatch.setattr(canary.controller, "OUT", canary.controller.OUT)
    monkeypatch.setattr(canary.controller, "PROTOCOL", canary.controller.PROTOCOL)
    canary.bind_live()
    assert runtime.OUT == tmp_path / "live"
    assert runtime.inputs is canary.live_inputs
    assert runtime.preflight is canary.live_preflight
    assert (runtime.FIXED_DENOMINATOR, runtime.TASK_CAP, runtime.BATCH_CAP, runtime.OUTPUT_CAP) == (3, 20000, 60000, 3000)
