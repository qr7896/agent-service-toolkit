import json

from evals.e1c_strict_v5_materialization_plan import build


def test_materialization_plan_is_blocked_without_certificate() -> None:
    plan = build(certificate={
        "ready": False,
        "reason": "identity_freeze_not_certified",
    })
    assert plan["ready"] is False
    assert plan["actions"] == []
    assert plan["provider_calls"] == 0


def test_materialization_plan_is_hashed_and_nonexecuting(tmp_path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "tasks": [
            {"instance_id": "a"}, {"instance_id": "b"}, {"instance_id": "c"},
        ]
    }), encoding="utf-8")
    certificate = {
        "ready": True,
        "manifest_sha256": "f" * 64,
        "source_revision": "rev",
    }
    plan = build(manifest, certificate=certificate)
    assert plan["ready"] is True
    assert len(plan["actions"]) == 3
    assert plan["task_content_materialized"] is False
    assert plan["provider_calls"] == 0
    assert len(plan["plan_sha256"]) == 64
