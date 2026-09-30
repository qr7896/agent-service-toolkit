"""Direct-only manifest transport must not inherit a configured proxy."""

from __future__ import annotations

import hashlib
import json

from evals import e1c_evaluation_2_canary_v2_stage as stage


def test_manifest_comparison_uses_no_proxy(tmp_path, monkeypatch):
    identity = tmp_path / "identity.json"
    identity.write_bytes(b"identity")
    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps({
        "identity_sha256": hashlib.sha256(b"identity").hexdigest(),
        "tasks": [
            {"instance_id": f"repo__project-{n}", "image": f"swebench/sweb.eval.x86_64.project_{n}:latest"}
            for n in range(3)
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(stage, "IDENTITY", identity)
    monkeypatch.setattr(stage, "METADATA", metadata)
    monkeypatch.setattr(stage, "TRANSPORT", tmp_path / "transport.json")
    calls = []

    def manifest(repository, *, mirror, proxy, mirror_host="docker.1ms.run"):
        calls.append((repository, mirror, proxy, mirror_host))
        return {"top_digest": "sha256:a", "platform_digest": "sha256:b", "compressed_layer_bytes": 1024}

    monkeypatch.setattr(stage, "_manifest", manifest)
    assert len(stage.audit_direct()["rows"]) == 3
    assert len(calls) == 6
    assert all(proxy is None for _, _, proxy, _ in calls)
    assert all(host == "docker.1panel.live" for _, mirror, _, host in calls if mirror)
